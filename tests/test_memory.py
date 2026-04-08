"""
tests/test_memory.py
====================
Unit tests لـ memory.py — تغطي كل edge cases.
"""

import json
from pathlib import Path

import pytest

from rafiq.memory import load_memory, remember, save_memory, update_session_stats


# ══════════════════════════════════════════════════════════════
#  Fixture: يعيّن MEMORY_FILE لمسار مؤقت في كل test
# ══════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def tmp_memory(tmp_path, monkeypatch):
    """كل test يشتغل بملف ذاكرة مؤقت منعزل."""
    mem_file = tmp_path / "test_memory.json"
    monkeypatch.setattr("rafiq.memory.MEMORY_FILE", mem_file)
    return mem_file


# ══════════════════════════════════════════════════════════════
#  load_memory
# ══════════════════════════════════════════════════════════════

class TestLoadMemory:

    def test_returns_defaults_when_file_missing(self):
        mem = load_memory()
        assert mem["user_name"]     == "سيدي"
        assert mem["city"]          == ""
        assert mem["preferences"]   == {}
        assert mem["total_sessions"] == 0

    def test_returns_defaults_when_file_empty(self, tmp_memory):
        tmp_memory.write_text("", encoding="utf-8")
        mem = load_memory()
        assert mem["user_name"] == "سيدي"

    def test_returns_defaults_when_json_corrupt(self, tmp_memory):
        tmp_memory.write_text("{ broken json !!!", encoding="utf-8")
        mem = load_memory()
        assert mem["user_name"] == "سيدي"

    def test_returns_defaults_when_json_is_not_dict(self, tmp_memory):
        tmp_memory.write_text("[1, 2, 3]", encoding="utf-8")
        mem = load_memory()
        assert mem["user_name"] == "سيدي"

    def test_loads_saved_name(self, tmp_memory):
        tmp_memory.write_text(
            json.dumps({"user_name": "أحمد"}, ensure_ascii=False),
            encoding="utf-8",
        )
        mem = load_memory()
        assert mem["user_name"] == "أحمد"

    def test_missing_keys_get_defaults(self, tmp_memory):
        """ملف موجود لكن ناقص بعض الـ keys → الـ defaults تتكمّل."""
        tmp_memory.write_text(
            json.dumps({"user_name": "سارة"}, ensure_ascii=False),
            encoding="utf-8",
        )
        mem = load_memory()
        assert mem["user_name"]   == "سارة"
        assert "city"             in mem
        assert "preferences"      in mem
        assert "total_sessions"   in mem

    def test_preserves_extra_keys(self, tmp_memory):
        """مفاتيح إضافية في الملف تتحفظ (لا تُمسح)."""
        data = {"user_name": "علي", "custom_key": "custom_val"}
        tmp_memory.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        mem = load_memory()
        assert mem.get("custom_key") == "custom_val"


# ══════════════════════════════════════════════════════════════
#  save_memory
# ══════════════════════════════════════════════════════════════

class TestSaveMemory:

    def test_saves_and_reloads(self, tmp_memory):
        mem = load_memory()
        mem["user_name"] = "فاطمة"
        save_memory(mem)
        reloaded = load_memory()
        assert reloaded["user_name"] == "فاطمة"

    def test_saves_arabic_without_escape(self, tmp_memory):
        mem = load_memory()
        mem["user_name"] = "محمد"
        save_memory(mem)
        raw = tmp_memory.read_text(encoding="utf-8")
        assert "محمد" in raw      # ensure_ascii=False
        assert "\\u" not in raw   # مش مُشفَّر


# ══════════════════════════════════════════════════════════════
#  remember
# ══════════════════════════════════════════════════════════════

class TestRemember:

    def test_remember_user_name(self):
        mem = load_memory()
        result = remember(mem, "user_name", "خالد")
        assert result["user_name"] == "خالد"

    def test_remember_city(self):
        mem = load_memory()
        result = remember(mem, "city", "الإسكندرية")
        assert result["city"] == "الإسكندرية"

    def test_remember_custom_key_goes_to_preferences(self):
        mem = load_memory()
        result = remember(mem, "favorite_color", "أزرق")
        assert result["preferences"]["favorite_color"] == "أزرق"

    def test_remember_returns_same_dict(self):
        mem = load_memory()
        result = remember(mem, "city", "القاهرة")
        assert result is mem   # in-place modification


# ══════════════════════════════════════════════════════════════
#  update_session_stats
# ══════════════════════════════════════════════════════════════

class TestUpdateSessionStats:

    def test_increments_total_sessions(self):
        mem = load_memory()
        assert mem["total_sessions"] == 0
        mem = update_session_stats(mem)
        assert mem["total_sessions"] == 1

    def test_sets_last_seen(self):
        mem = load_memory()
        assert mem["last_seen"] == ""
        mem = update_session_stats(mem)
        assert mem["last_seen"] != ""
        assert "-" in mem["last_seen"]   # YYYY-MM-DD format
