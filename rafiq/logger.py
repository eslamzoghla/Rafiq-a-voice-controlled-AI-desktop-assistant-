"""
rafiq/logger.py
===============
سجل المحادثات — يكتب في ملف نصي بتنسيق ثابت.
"""

from datetime import datetime
from .config import LOG_FILE


def log(role: str, text: str) -> None:
    """كتابة سطر في السجل. بيفشل بصمت لو مفيش صلاحيات."""
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{ts}] {role}: {text}\n")
    except OSError:
        pass
