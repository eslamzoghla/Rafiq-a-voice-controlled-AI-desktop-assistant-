"""
rafiq/llm.py
============
RafiqSession — يحتوي على كل state المحادثة.
RafiqSession — Contains all conversation state.
يحل مشكلة الـ globals ويسهّل الـ testing.
Solves global state issues and enables easy testing.

_call_llm() منفصلة ويمكن mock-ها في الـ tests.
_call_llm() is separate and can be mocked in tests.
"""

import textwrap
from typing import Optional

from openai import OpenAI

from .config import (
    FALLBACK_MODEL, MAX_HISTORY, PREFERRED_LANGUAGE,
    OPENROUTER_API_KEY, PRIMARY_MODEL,
)
from .i18n import get_system_prompt, detect_language
from .logger import log
from .memory import save_memory


# ── OpenRouter client (singleton) ─────────────────────────────
_client: Optional[OpenAI] = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
            default_headers={
                "HTTP-Referer": "https://github.com/rafiq-ai",
                "X-Title":      "RAFIQ-v2-Windows-Assistant",
            },
        )
    return _client


# ══════════════════════════════════════════════════════════════
#  System Prompt (Language-Aware)
# ══════════════════════════════════════════════════════════════

def build_system_prompt(mem: dict, language: str = PREFERRED_LANGUAGE) -> str:
    """
    Build language-aware system prompt.
    
    Args:
        mem: Memory dictionary with user info
        language: Language code ('ar' or 'en')
    
    Returns:
        System prompt formatted with user info
    """
    city = mem.get("city", "")
    return get_system_prompt(
        language,
        user_name=mem.get("user_name", "User"),
        total_sessions=mem.get("total_sessions", 0),
        city=city
    )


# ══════════════════════════════════════════════════════════════
#  الدالة الجوهرية للـ LLM call
# ══════════════════════════════════════════════════════════════

def _call_llm(model: str, messages: list,
              temperature: float = 0.25,
              max_tokens: int = 400,
              language: str = PREFERRED_LANGUAGE) -> Optional[str]:
    """
    استدعاء نموذج واحد — Call a single LLM model.
    يرجع نص الرد أو None عند الفشل — Returns reply text or None on failure.
    الـ exceptions تُسجَّل ولا تُرمى — Exceptions are logged, not raised.
    """
    try:
        resp = get_client().chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        reply = (resp.choices[0].message.content or "").strip()
        return reply if reply else None
    except Exception as e:
        err = str(e)
        if language == "ar":
            print(f"⚠️  [{model}] فشل: {err[:120]}")
            if "401" in err:
                return "CHAT|فشل التحقق من الهوية. راجع مفتاح API."
            if "429" in err:
                return "CHAT|تجاوزنا حد الطلبات. انتظر لحظة."
        else:
            print(f"⚠️  [{model}] Failed: {err[:120]}")
            if "401" in err:
                return "CHAT|Authentication failed. Check your API key."
            if "429" in err:
                return "CHAT|Rate limit exceeded. Please wait."
        return None


# ══════════════════════════════════════════════════════════════
#  RafiqSession
# ══════════════════════════════════════════════════════════════

class RafiqSession:
    """
    يحمل كل state المحادثة في object واحد — Holds all conversation state.
    - لا globals — No globals
    - قابل للـ testing بسهولة — Easy testing (can inject mock client)
    - يدعم multi-instance مستقبلاً — Supports multi-instance in future
    """

    def __init__(self, memory: dict, client: Optional[OpenAI] = None, language: str = PREFERRED_LANGUAGE):
        self.memory: dict          = memory
        self.history: list         = []
        self.first_message: bool   = True
        self._client               = client or get_client()
        self.language: str         = memory.get("language", language)

    # ── Properties ───────────────────────────────────────────

    @property
    def user_name(self) -> str:
        # Support both Arabic and English default names
        default_name = "User" if self.language == "en" else "سيدي"
        return self.memory.get("user_name", default_name)

    # ── المحادثة ── Conversation ──────────────────────────────

    def ask(self, user_text: str) -> str:
        """
        إرسال رسالة المستخدم والحصول على رد LLM — Send user message and get LLM reply.
        يرجع الرد الخام (ACTION: ... / CHAT|...) لتنفيذه في actions.py
        Returns raw reply (ACTION: ... / CHAT|...) for execution in actions.py
        """
        if not user_text or not user_text.strip():
            if self.language == "ar":
                return f"CHAT|لم أسمع شيئاً يا {self.user_name}، هل يمكنك الإعادة؟"
            else:
                return f"CHAT|I didn't hear anything, {self.user_name}. Can you repeat?"

        # ── تسجيل رسالة المستخدم — Log user message ────────────
        self.history.append({"role": "user", "content": user_text.strip()})
        self.history = _trim_history(self.history, MAX_HISTORY)
        log("USER", user_text)

        # ── بناء messages — Build messages ─────────────────────
        messages = (
            [{"role": "system", "content": build_system_prompt(self.memory, self.language)}]
            + self.history
        )

        # ── محاولة النماذج بالترتيب — Try models in order ────────
        reply = None
        for model in (PRIMARY_MODEL, FALLBACK_MODEL):
            reply = _call_llm(model, messages, language=self.language)
            if reply:
                break

        if not reply:
            if self.language == "ar":
                reply = f"CHAT|عذراً يا {self.user_name}، لا أملك إجابة الآن."
            else:
                reply = f"CHAT|Sorry {self.user_name}, I don't have an answer right now."

        # ── حفظ رد المساعد في الـ history — Save assistant reply ───
        self.history.append({"role": "assistant", "content": reply})
        log("RAFIQ", reply)

        return reply

    def greet_new_user(self) -> Optional[str]:
        """
        طلب الاسم عند أول تحية — Ask for name on first greeting — فقط لو الاسم مش محفوظ
        Only if name not already saved. Returns greeting or None if not time to greet.
        Updates and saves memory.
        """
        default_name = "User" if self.language == "en" else "سيدي"
        if self.memory["user_name"] != default_name and self.memory["user_name"] != "User" and self.memory["user_name"] != "سيدي":
            return None      # الاسم محفوظ مسبقاً — Name already saved

        if self.language == "ar":
            name = input("\n🤖 رفيق: أهلاً! ما اسمك من فضلك؟\n   اكتب اسمك: ").strip()
            if name:
                self.memory["user_name"] = name
                self.memory["total_sessions"] += 1
                save_memory(self.memory)
                return f"CHAT|أهلاً يا {name}! أنا رفيق مساعدك الذكي، كيف أقدر أساعدك؟"
            return "CHAT|أهلاً! أنا رفيق، كيف أساعدك؟"
        else:
            name = input("\n🤖 Rafiq: Hello! What's your name please?\n   Enter your name: ").strip()
            if name:
                self.memory["user_name"] = name
                self.memory["total_sessions"] += 1
                save_memory(self.memory)
                return f"CHAT|Hello {name}! I'm Rafiq, your smart assistant. How can I help you?"
            return "CHAT|Hello! I'm Rafiq. How can I help?"


# ══════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════

def _trim_history(history: list, max_turns: int) -> list:
    """يحتفظ بآخر max_turns جولة (= max_turns*2 message)."""
    max_msgs = max_turns * 2
    return history[-max_msgs:] if len(history) > max_msgs else history
