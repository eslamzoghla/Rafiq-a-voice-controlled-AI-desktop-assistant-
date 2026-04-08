"""
rafiq/stt.py
============
نظام STT — استماع من الميكروفون مع:
  - Calibration caching (مرة كل 5 دقايق بدل كل مرة)
  - إعادة المحاولة التلقائية
  - دعم عدة لهجات عربية
  - Whisper fallback (لو OPENAI_API_KEY متاح)
"""

import os
import tempfile
import time
from pathlib import Path
from typing import Optional

import speech_recognition as sr

from .config import (
    STT_CALIBRATION_TTL, STT_ENERGY_THRESHOLD,
    STT_LANGUAGES, STT_PAUSE_THRESHOLD,
    STT_PHRASE_LIMIT, STT_TIMEOUT,
)
from .logger import log


# ── Recognizer (singleton) ─────────────────────────────────────
_recognizer                         = sr.Recognizer()
_recognizer.pause_threshold         = STT_PAUSE_THRESHOLD
_recognizer.energy_threshold        = STT_ENERGY_THRESHOLD
_recognizer.dynamic_energy_threshold = True
_recognizer.non_speaking_duration   = 0.25

# ── Calibration cache ─────────────────────────────────────────
_last_calibration: float = 0.0


def _maybe_calibrate(src: sr.Microphone) -> None:
    """إعادة الكاليبريشن كل STT_CALIBRATION_TTL ثانية فقط."""
    global _last_calibration
    now = time.monotonic()
    if (now - _last_calibration) >= STT_CALIBRATION_TTL:
        _recognizer.adjust_for_ambient_noise(src, duration=0.8)
        _last_calibration = now


# ══════════════════════════════════════════════════════════════
#  Whisper fallback
# ══════════════════════════════════════════════════════════════

def _transcribe_with_whisper(audio: sr.AudioData) -> Optional[str]:
    """
    محاولة التعرف باستخدام Whisper (OpenAI).
    يرجع None لو المفتاح غير موجود أو فشل.
    """
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return None

    tmp_path: Optional[Path] = None
    try:
        from openai import OpenAI
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio.get_wav_data())
            tmp_path = Path(f.name)

        client = OpenAI(api_key=api_key)
        with open(tmp_path, "rb") as f:
            resp = client.audio.transcriptions.create(
                file=f,
                model="whisper-1",
                response_format="text",
            )

        if hasattr(resp, "text"):
            return resp.text
        if isinstance(resp, str):
            return resp
        return None
    except Exception as e:
        print(f"⚠️  خطأ في Whisper STT: {e}")
        return None
    finally:
        if tmp_path:
            tmp_path.unlink(missing_ok=True)


# ══════════════════════════════════════════════════════════════
#  الاستماع الرئيسي
# ══════════════════════════════════════════════════════════════

def listen(retries: int = 2) -> str:
    """
    الاستماع من الميكروفون.
    يرجع النص المُتعرَّف عليه أو "" عند الفشل.
    """
    try:
        mic_list = sr.Microphone.list_microphone_names()
        if not mic_list:
            print("❌  لا توجد ميكروفونات متاحة.")
            return ""
    except Exception as e:
        print(f"❌  خطأ في الميكروفون: {e}")
        return ""

    for attempt in range(retries):
        # ── التقاط الصوت ──────────────────────────────────────
        audio: Optional[sr.AudioData] = None
        try:
            with sr.Microphone() as src:
                label = (
                    "🎙️  يستمع..."
                    if attempt == 0
                    else f"🎙️  إعادة المحاولة ({attempt + 1}/{retries})..."
                )
                print(label)
                _maybe_calibrate(src)
                audio = _recognizer.listen(
                    src,
                    timeout=STT_TIMEOUT,
                    phrase_time_limit=STT_PHRASE_LIMIT,
                )
        except sr.WaitTimeoutError:
            if attempt < retries - 1:
                print("⏱️  لم يُسمع شيء، أحاول مرة أخرى...")
                continue
            print("⏱️  انتهت مهلة الاستماع.")
            return ""
        except Exception as e:
            print(f"❌  خطأ في الميكروفون: {e}")
            return ""

        # ── التعرف على الكلام ─────────────────────────────────
        print("🔄  التعرف على الكلام...")

        for lang in STT_LANGUAGES:
            try:
                text = _recognizer.recognize_google(audio, language=lang)
                print(f"✅  ({lang}): {text}")
                log("USER_VOICE", text)
                return text
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                print(f"⚠️  خطأ في خدمة STT: {e}")
                break   # مشكلة شبكة — لا فائدة من تجربة لغات أخرى

        # ── Whisper fallback ───────────────────────────────────
        if audio is not None:
            whisper_text = _transcribe_with_whisper(audio)
            if whisper_text:
                print(f"✅  (whisper): {whisper_text}")
                log("USER_VOICE", whisper_text)
                return whisper_text

        if attempt < retries - 1:
            print("❓  لم يُفهم الكلام، أحاول مرة أخرى...")
        else:
            print("❓  لم يُفهم الكلام.")

    return ""
