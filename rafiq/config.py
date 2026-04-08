"""
rafiq/config.py
===============
كل الإعدادات والثوابت في مكان واحد.
غيّر هنا فقط — لا تفتح ملفات تانية للإعدادات.
"""

import os
from pathlib import Path

# ── Language Configuration ────────────────────────────────────
# Set preferred language: "ar" (Arabic) or "en" (English)
# Can also be auto-detected from user input
PREFERRED_LANGUAGE: str = os.environ.get("RAFIQ_LANGUAGE", "en")  # Default: English
AUTO_DETECT_LANGUAGE: bool = True  # Auto-detect from user input if True

# ── API Keys ──────────────────────────────────────────────────
OPENROUTER_API_KEY: str = os.environ.get("OPENROUTER_API_KEY", "")

# ── النماذج ───────────────────────────────────────────────────
PRIMARY_MODEL  = "openai/gpt-4o-mini"
FALLBACK_MODEL = "openai/gpt-3.5-turbo"
VISION_MODEL   = "openai/gpt-4o-mini"

# ── TTS ───────────────────────────────────────────────────────
# Language-aware TTS settings: maps language to Google TTS language code
TTS_VOICES = {
    "ar": "ar",      # Arabic
    "en": "en",      # English
}
TTS_RATE = "+5%"
TTS_MAX_CHARS = 400  # Character limit per TTS call

# ── STT ───────────────────────────────────────────────────────
# Multi-language STT support (Google Speech Recognition)
STT_LANGUAGES = ("ar-EG", "ar-SA", "en-US", "en-GB")
STT_PAUSE_THRESHOLD  = 1.8
STT_ENERGY_THRESHOLD = 300
STT_TIMEOUT          = 8
STT_PHRASE_LIMIT     = 30
STT_CALIBRATION_TTL  = 300  # Recalibrate microphone every 5 minutes

# ── المحادثة ──────────────────────────────────────────────────
MAX_HISTORY = 6               # جولات محادثة (× 2 = عدد messages)

# ── الملفات ───────────────────────────────────────────────────
MEMORY_FILE = Path("rafiq_memory.json")
LOG_FILE    = Path("rafiq_log.txt")

# ── Security: أوامر CMD مسموح بيها فقط ───────────────────────
# Allowlist صريحة — أي أمر مش هنا محظور تلقائياً
SAFE_CMD_ALLOWLIST: frozenset[str] = frozenset({
    "ipconfig", "ping", "dir", "echo", "type",
    "systeminfo", "tasklist", "ver", "whoami",
    "hostname", "netstat", "tracert", "nslookup",
    "date", "time", "vol", "chkdsk", "sfc",
})

# ── Exit Words (Arabic & English) ─────────────────────────────
EXIT_WORDS: frozenset[str] = frozenset({
    # English
    "exit", "quit", "bye", "goodbye", "stop",
    # Arabic
    "خروج", "إنهاء", "وقف", "خلاص", "قفل",
})

# ── APP_MAP الثابتة (fallback لو الـ registry فشل) ───────────
STATIC_APP_MAP: dict[str, str] = {
    # متصفحات
    "chrome": "chrome",       "كروم": "chrome",
    "firefox": "firefox",     "فايرفوكس": "firefox",
    "edge": "msedge",         "ايدج": "msedge",
    # أوفيس
    "word": "winword",        "وورد": "winword",   "الورد": "winword",
    "excel": "excel",         "اكسل": "excel",     "الاكسل": "excel",
    "powerpoint": "powerpnt", "بوربوينت": "powerpnt",
    # نظام
    "notepad": "notepad",     "مفكرة": "notepad",
    "calculator": "calc",     "حاسبة": "calc",
    "explorer": "explorer",   "مستكشف": "explorer",
    "cmd": "cmd",
    "task manager": "taskmgr","مدير المهام": "taskmgr",
    "paint": "mspaint",       "رسام": "mspaint",
    "settings": "ms-settings:","الإعدادات": "ms-settings:",
    # ترفيه
    "spotify": "spotify",     "سبوتيفاي": "spotify",
    "vlc": "vlc",
    "discord": "discord",     "ديسكورد": "discord",
    # أدوات
    "vscode": "code",         "vs code": "code",
    "telegram": "telegram",   "تيليجرام": "telegram",
    "whatsapp": "https://web.whatsapp.com",
    "واتساب": "https://web.whatsapp.com",
    "zoom": "zoom",
    "obs": "obs64",
}
