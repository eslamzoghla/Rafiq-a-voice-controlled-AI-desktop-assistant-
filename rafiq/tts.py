"""
rafiq/tts.py
============
نظام TTS — Text-to-speech system — تحويل النص لصوت بدون disk I/O.
بدون disk I/O — without disk I/O. Used BytesIO directly with pygame.
يستخدم BytesIO مباشرة مع pygame.
"""

import io
import time
from typing import Optional

from gtts import gTTS
import pygame

from .config import TTS_MAX_CHARS, TTS_RATE, TTS_VOICES, PREFERRED_LANGUAGE
from .i18n import detect_language
from .logger import log


# ── تهيئة الصوت — Initialize audio ────────────────────────────
try:
    pygame.mixer.init()
    _mixer_ok = True
except Exception as e:
    print(f"⚠️  تحذير — Warning: تعذّر تهيئة الصوت — Audio init failed: {e}")
    _mixer_ok = False


# ══════════════════════════════════════════════════════════════
#  توليد الصوت في الذاكرة — Audio synthesis in memory (بدون disk)
# ══════════════════════════════════════════════════════════════

def _synthesize_to_bytes(text: str, language: str = PREFERRED_LANGUAGE) -> Optional[bytes]:
    """
    تحويل النص لـ bytes صوتية في الذاكرة — Convert text to audio bytes.
    يرجع None عند الفشل — Returns None on failure.
    """
    try:
        # Get language code from TTS_VOICES dict
        if language not in TTS_VOICES:
            language = PREFERRED_LANGUAGE
        lang_code = TTS_VOICES[language]
        
        tts = gTTS(text=text, lang=lang_code, slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
        if language == "ar":
            print(f"⚠️  خطأ في توليد الصوت: {e}")
        else:
            print(f"⚠️  Error in audio generation: {e}")
        return None


# ══════════════════════════════════════════════════════════════
#  النطق — Speech output
# ══════════════════════════════════════════════════════════════

def speak(text: str, language: Optional[str] = None) -> None:
    """
    نطق النص بالصوت — Speak text aloud.
    - يطبع النص على الشاشة دائماً — Always prints text to screen.
    - يقتصر النطق على TTS_MAX_CHARS حرف — Limits speech to TTS_MAX_CHARS.
    - يفشل بصمت لو pygame مش شغّال — Fails silently if pygame not active.
    - Auto-detects language if not specified — يكتشف اللغة تلقائياً
    """
    if not text or not text.strip():
        return

    # Auto-detect language if not provided
    if language is None:
        language = detect_language(text)
    
    spoken = text[:TTS_MAX_CHARS] + ("..." if len(text) > TTS_MAX_CHARS else "")
    
    if language == "ar":
        print(f"\n🤖 رفيق: {text}\n")
    else:
        print(f"\n🤖 Rafiq: {text}\n")
    
    log("RAFIQ_SPEAK", text[:200])

    if not _mixer_ok:
        return

    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()

        audio_bytes = _synthesize_to_bytes(spoken, language)
        if not audio_bytes:
            if language == "ar":
                print("⚠️  لم يُنتج صوت.")
            else:
                print("⚠️  No audio produced.")
            return

        buf = io.BytesIO(audio_bytes)
        pygame.mixer.music.load(buf)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            time.sleep(0.1)

        pygame.mixer.music.unload()

    except Exception as e:
        if language == "ar":
            print(f"⚠️  خطأ في الصوت: {e}")
        else:
            print(f"⚠️  Audio error: {e}")
