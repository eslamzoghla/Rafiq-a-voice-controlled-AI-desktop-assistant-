"""
rafiq/actions.py
================
تنفيذ الأوامر — الوسيط بين الـ LLM والنظام.

كل action بترجع string يوصف ما حصل.
لو في error → ترجع رسالة عربية واضحة (مش تتجاهله).
"""

import os
import subprocess
import time
import webbrowser
from urllib.parse import quote

from .apps    import resolve_app
from .config  import SAFE_CMD_ALLOWLIST
from .memory  import remember, save_memory
from .tools   import (
    file_create, file_delete, file_list, file_read,
    get_news, get_weather, take_screenshot,
)


# ── الـ actions اللي نتيجتها تُنطق للمستخدم ──────────────────
SPOKEN_ACTIONS: frozenset[str] = frozenset({
    "CHAT", "WEATHER", "NEWS", "FILE_READ", "FILE_LIST", "SCREENSHOT",
})


def execute_action(action_type: str, details: str,
                   memory: dict, llm_client=None) -> tuple[str, bool]:
    """
    تنفيذ action واحدة.

    Returns:
        (result_text, should_speak)
        should_speak=True  → النتيجة تُنطق للمستخدم
        should_speak=False → نفّذنا بصمت (OPEN_URL مثلاً)
                             إلا لو في error
    """
    action_type = action_type.strip().upper()
    details     = details.strip()
    user_name   = memory.get("user_name", "سيدي")

    # ─ OPEN_URL ────────────────────────────────────────────────
    if action_type == "OPEN_URL":
        url = details if details.startswith("http") else f"https://{details}"
        try:
            webbrowser.open(url)
            return f"تم فتح {url}.", False
        except Exception as e:
            return f"تعذّر فتح الرابط: {e}", True

    # ─ SEARCH_GOOGLE ───────────────────────────────────────────
    elif action_type == "SEARCH_GOOGLE":
        webbrowser.open(f"https://www.google.com/search?q={quote(details)}")
        return f"جارٍ البحث عن '{details}' في جوجل.", False

    # ─ SEARCH_YOUTUBE ──────────────────────────────────────────
    elif action_type == "SEARCH_YOUTUBE":
        webbrowser.open(f"https://www.youtube.com/results?search_query={quote(details)}")
        return f"جارٍ البحث عن '{details}' في يوتيوب.", False

    # ─ OPEN_APP ────────────────────────────────────────────────
    elif action_type == "OPEN_APP":
        exe = resolve_app(details)

        if exe is None:
            return (
                f"لم أجد برنامج '{details}' على جهازك يا {user_name}. "
                f"تأكد إنه مثبت أو قل الاسم الإنجليزي.",
                True,
            )

        if exe.startswith("http"):
            webbrowser.open(exe)
        elif exe.startswith("ms-"):
            subprocess.Popen(f"start {exe}", shell=True)
        elif exe.endswith(".lnk"):
            # Start Menu shortcut
            os.startfile(exe)
        else:
            try:
                if os.name == "nt":
                    subprocess.Popen(f'start "" "{exe}"', shell=True)
                else:
                    subprocess.Popen(exe, shell=True,
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)
            except Exception as e:
                try:
                    os.startfile(exe)
                except Exception as e2:
                    return f"تعذّر فتح {details}: {e} / {e2}", True

        return f"تم فتح {details}.", False

    # ─ TYPE_TEXT ───────────────────────────────────────────────
    elif action_type == "TYPE_TEXT":
        try:
            import pyautogui, pyperclip
            time.sleep(0.6)
            pyperclip.copy(details)
            pyautogui.hotkey("ctrl", "v")
            return "تم كتابة النص.", False
        except ImportError:
            return "مكتبة pyautogui/pyperclip غير مثبتة. شغّل: pip install pyautogui pyperclip", True
        except Exception as e:
            return f"تعذّر كتابة النص: {e}", True

    # ─ PRESS_KEY ───────────────────────────────────────────────
    elif action_type == "PRESS_KEY":
        try:
            import pyautogui
            time.sleep(0.3)
            pyautogui.hotkey(*details.split("+"))
            return f"تم الضغط على {details}.", False
        except ImportError:
            return "مكتبة pyautogui غير مثبتة.", True
        except Exception as e:
            return f"تعذّر الضغط على {details}: {e}", True

    # ─ RUN_CMD (Allowlist) ─────────────────────────────────────
    elif action_type == "RUN_CMD":
        base_cmd = details.strip().lower().split()[0] if details.strip() else ""
        if base_cmd not in SAFE_CMD_ALLOWLIST:
            return (
                f"هذا الأمر غير مسموح به يا {user_name}. "
                f"الأوامر المتاحة: {', '.join(sorted(SAFE_CMD_ALLOWLIST))}.",
                True,
            )
        try:
            result = subprocess.run(
                details, shell=True, capture_output=True,
                text=True, timeout=10,
            )
            out = (result.stdout or result.stderr or "").strip()
            return (f"النتيجة: {out[:300]}" if out else "تم تنفيذ الأمر.", True)
        except subprocess.TimeoutExpired:
            return "انتهت مهلة الأمر.", True
        except Exception as e:
            return f"خطأ في تنفيذ الأمر: {e}", True

    # ─ SCREENSHOT ──────────────────────────────────────────────
    elif action_type == "SCREENSHOT":
        result = take_screenshot(mode=details.lower(), llm_client=llm_client)
        return result, True

    # ─ FILE_CREATE ─────────────────────────────────────────────
    elif action_type == "FILE_CREATE":
        parts = details.split("|", 1)
        if len(parts) < 2:
            return "تنسيق خاطئ: FILE_CREATE|<مسار>|<محتوى>", True
        result = file_create(parts[0].strip(), parts[1])
        return result, True

    # ─ FILE_READ ───────────────────────────────────────────────
    elif action_type == "FILE_READ":
        content = file_read(details)
        print(f"\n📄 محتوى الملف:\n{content}\n")
        return content, True

    # ─ FILE_DELETE ─────────────────────────────────────────────
    elif action_type == "FILE_DELETE":
        result = file_delete(details)
        return result, True

    # ─ FILE_LIST ───────────────────────────────────────────────
    elif action_type == "FILE_LIST":
        listing = file_list(details or ".")
        print(f"\n📁 محتويات المجلد:\n{listing}\n")
        return listing, True

    # ─ WEATHER ─────────────────────────────────────────────────
    elif action_type == "WEATHER":
        city = details or memory.get("city") or "Cairo"
        result = get_weather(city)
        print(f"\n🌤️  الطقس: {result}\n")
        return result, True

    # ─ NEWS ────────────────────────────────────────────────────
    elif action_type == "NEWS":
        result = get_news(details or "عام")
        print(f"\n📰 الأخبار:\n{result}\n")
        # نقرأ أول 3 أسطر فقط
        lines  = result.splitlines()
        spoken = " ".join(lines[:3])
        return spoken, True

    # ─ REMEMBER ────────────────────────────────────────────────
    elif action_type == "REMEMBER":
        parts = details.split("|", 1)
        if len(parts) != 2:
            return "تنسيق خاطئ للأمر REMEMBER: REMEMBER|<مفتاح>|<قيمة>", True
        key, val = parts[0].strip(), parts[1].strip()
        remember(memory, key, val)
        save_memory(memory)
        return f"تم حفظ {key}.", False

    # ─ CHAT ────────────────────────────────────────────────────
    elif action_type == "CHAT":
        return details, True

    # ─ Unknown ─────────────────────────────────────────────────
    else:
        return f"أمر غير معروف: {action_type}", True


# ══════════════════════════════════════════════════════════════
#  Parser
# ══════════════════════════════════════════════════════════════

def parse_and_execute(llm_response: str, memory: dict,
                      llm_client=None) -> str:
    """
    تحليل رد LLM وتنفيذ كل الأوامر فيه.
    بيرجع النص المجمّع المراد نطقه.

    يتعامل مع:
      - سطور ACTION: <TYPE>|<details>
      - سطور <TYPE>|<details> بدون ACTION: (بعض النماذج بتحذفها)
      - نص عادي (بيتضاف مباشرة للنطق)
      - أوامر بتنسيق خاطئ (تُبلّغ المستخدم)
    """
    import re

    if not llm_response or not llm_response.strip():
        return f"تم يا {memory.get('user_name', 'سيدي')}."

    lines      = llm_response.strip().splitlines()
    chat_parts: list[str] = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # ── استخراج الـ payload ───────────────────────────────
        if line.upper().startswith("ACTION:"):
            payload = line[len("ACTION:"):].strip()
        elif re.match(r'^[A-Z_]{2,}\|', line):
            # سطر بدون "ACTION:" — بعض النماذج بتبعت كده
            payload = line
        else:
            # نص عادي — يُضاف مباشرة
            chat_parts.append(line)
            continue

        # ── تنفيذ الأمر ───────────────────────────────────────
        if "|" not in payload:
            chat_parts.append(f"تنسيق خاطئ: {payload}")
            continue

        action_type, details = payload.split("|", 1)
        action_type = action_type.strip()
        details     = details.strip()

        if not action_type:
            chat_parts.append("أمر فارغ في الرد.")
            continue

        result, should_speak = execute_action(
            action_type, details, memory, llm_client
        )

        if should_speak:
            chat_parts.append(result)
        elif _is_error(result):
            # حتى لو الأمر مش مفروض ينطق، الـ errors دايماً تتبلّغ
            chat_parts.append(result)

    final = " ".join(p for p in chat_parts if p).strip()
    return final or f"تم يا {memory.get('user_name', 'سيدي')}."


def _is_error(text: str) -> bool:
    """هل النص يحتوي على رسالة خطأ؟"""
    error_markers = ("تعذّر", "خطأ", "غير موجود", "غير مسموح", "فشل", "مثبت")
    return any(m in text for m in error_markers)
