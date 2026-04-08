"""
rafiq/apps.py
=============
Dynamic discovery للبرامج المثبتة على Windows.
يقرأ من:
  1. Windows Registry (App Paths)
  2. Start Menu shortcuts (.lnk)
  3. الـ STATIC_APP_MAP كـ fallback

النتيجة: dict يربط اسم البرنامج (lowercase) بالـ executable path.
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional

from .config import STATIC_APP_MAP

# ── Cache ──────────────────────────────────────────────────────
_app_cache: dict[str, str] = {}
_cache_built_at: float = 0.0
_CACHE_TTL = 300.0   # إعادة البناء كل 5 دقايق


# ── Registry discovery (Windows only) ─────────────────────────

def _discover_from_registry() -> dict[str, str]:
    """يقرأ HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths"""
    if sys.platform != "win32":
        return {}
    try:
        import winreg
    except ImportError:
        return {}

    result: dict[str, str] = {}
    reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"

    for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            with winreg.OpenKey(hive, reg_path) as base:
                i = 0
                while True:
                    try:
                        sub_name = winreg.EnumKey(base, i)
                        i += 1
                        with winreg.OpenKey(base, sub_name) as sub:
                            try:
                                exe_path, _ = winreg.QueryValueEx(sub, "")
                                if exe_path:
                                    # مفتاح بدون extension كـ alias
                                    clean = sub_name.lower().replace(".exe", "")
                                    result[clean] = exe_path
                                    result[sub_name.lower()] = exe_path
                            except OSError:
                                pass
                    except OSError:
                        break
        except OSError:
            continue

    return result


def _discover_from_start_menu() -> dict[str, str]:
    """يقرأ shortcuts من Start Menu ويستخرج اسم البرنامج."""
    if sys.platform != "win32":
        return {}

    result: dict[str, str] = {}
    start_menu_dirs = [
        Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
        Path(os.environ.get("PROGRAMDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
    ]

    for smd in start_menu_dirs:
        if not smd.exists():
            continue
        for lnk in smd.rglob("*.lnk"):
            # استخدام اسم الملف بدون extension كـ alias
            name = lnk.stem.lower().strip()
            if name and name not in result:
                # نحفظ الـ path للـ shortcut — Windows بيشغّله مباشرة
                result[name] = str(lnk)

    return result


def _build_app_map() -> dict[str, str]:
    """بناء الـ app map الكامل من كل المصادر."""
    combined: dict[str, str] = {}

    # 1. Static map كـ base (الأقل أولوية)
    combined.update({k.lower(): v for k, v in STATIC_APP_MAP.items()})

    # 2. Start Menu shortcuts
    combined.update(_discover_from_start_menu())

    # 3. Registry (أعلى أولوية — أدق)
    combined.update(_discover_from_registry())

    return combined


def get_app_map() -> dict[str, str]:
    """
    إرجاع الـ app map مع caching.
    يُعيد البناء كل 5 دقايق تلقائياً.
    """
    global _app_cache, _cache_built_at
    now = time.monotonic()
    if not _app_cache or (now - _cache_built_at) > _CACHE_TTL:
        _app_cache = _build_app_map()
        _cache_built_at = now
    return _app_cache


def resolve_app(name: str) -> Optional[str]:
    """
    إيجاد الـ executable لاسم برنامج معيّن.
    بيجرب:
      1. مطابقة تامة (case-insensitive)
      2. بعد حذف "ال" من أول الكلمة (عربي)
      3. Substring match (الاسم موجود جوه مفتاح أطول)
    يرجع None لو مش لاقي.
    """
    app_map = get_app_map()
    key = name.lower().strip()

    # 1. مطابقة تامة
    if key in app_map:
        return app_map[key]

    # 2. حذف "ال" (عربي)
    if key.startswith("ال") and key[2:] in app_map:
        return app_map[key[2:]]

    # 3. Substring match — الاسم جزء من مفتاح موجود
    for map_key, exe in app_map.items():
        if key in map_key or map_key in key:
            return exe

    return None


def invalidate_cache() -> None:
    """مسح الـ cache — مفيد للـ testing."""
    global _app_cache, _cache_built_at
    _app_cache = {}
    _cache_built_at = 0.0
