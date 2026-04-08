"""
rafiq/memory.py
===============
إدارة الذاكرة الدائمة — تحميل، حفظ، تحديث.
معزولة تماماً عن باقي الكود.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import MEMORY_FILE


_DEFAULTS: dict[str, Any] = {
    "user_name":     "سيدي",
    "city":          "",
    "preferences":   {},
    "total_sessions": 0,
    "last_seen":     "",
}


def load_memory() -> dict:
    """
    تحميل الذاكرة من الملف.
    لو الملف مش موجود أو JSON فاسد → ترجع القيم الافتراضية.
    لو الملف ناقص بعض الـ keys → تتكمّل بالقيم الافتراضية.
    """
    result = dict(_DEFAULTS)
    if not MEMORY_FILE.exists():
        return result
    try:
        raw = MEMORY_FILE.read_text(encoding="utf-8")
        if not raw.strip():
            return result                      # ملف فاضي
        data = json.loads(raw)
        if not isinstance(data, dict):
            return result                      # JSON صح بس مش dict
        result.update(data)
    except (json.JSONDecodeError, OSError):
        pass                                   # ملف فاسد → defaults
    return result


def save_memory(mem: dict) -> None:
    """
    حفظ الذاكرة إلى الملف.
    بيكتب atomically قدر الإمكان (write إلى temp ثم rename).
    """
    tmp = MEMORY_FILE.with_suffix(".tmp")
    try:
        tmp.write_text(
            json.dumps(mem, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(MEMORY_FILE)
    except OSError as e:
        print(f"⚠️  تعذّر حفظ الذاكرة: {e}")
        tmp.unlink(missing_ok=True)


def update_session_stats(mem: dict) -> dict:
    """تحديث إحصائيات الجلسة — بيرجع نسخة معدّلة."""
    mem["total_sessions"] += 1
    mem["last_seen"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    return mem


def remember(mem: dict, key: str, value: str) -> dict:
    """
    حفظ معلومة في الذاكرة.
    المفاتيح المعروفة (user_name, city) تتحفظ مباشرة.
    أي مفتاح تاني يتحفظ في preferences.
    """
    if key == "user_name":
        mem["user_name"] = value
    elif key == "city":
        mem["city"] = value
    else:
        mem.setdefault("preferences", {})[key] = value
    return mem
