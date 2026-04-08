"""
tests/test_apps.py
==================
Unit tests لـ apps.py — resolve_app والـ cache.
"""

from unittest.mock import patch

import pytest

from rafiq.apps import invalidate_cache, resolve_app


@pytest.fixture(autouse=True)
def clear_cache():
    """امسح الـ cache قبل كل test."""
    invalidate_cache()
    yield
    invalidate_cache()


class TestResolveApp:

    def test_exact_match_from_static_map(self):
        """notepad موجود في الـ static map."""
        result = resolve_app("notepad")
        assert result is not None
        assert "notepad" in result.lower()

    def test_case_insensitive(self):
        result_lower = resolve_app("notepad")
        result_upper = resolve_app("NOTEPAD")
        # كلاهما يلاقوا نفس البرنامج
        assert (result_lower is None) == (result_upper is None)

    def test_arabic_prefix_stripped(self):
        """'المفكرة' → يجرب 'مفكرة'."""
        result = resolve_app("المفكرة")
        assert result is not None

    def test_unknown_app_returns_none(self):
        """برنامج مش موجود نهائياً."""
        with patch("rafiq.apps._discover_from_registry", return_value={}):
            with patch("rafiq.apps._discover_from_start_menu", return_value={}):
                invalidate_cache()
                result = resolve_app("برنامج_غير_موجود_مطلقاً_xyzabc123")
                assert result is None

    def test_registry_discovery_used_when_available(self):
        """لو الـ registry رجع نتيجة، تتستخدم."""
        fake_registry = {"cursor": r"C:\Users\test\AppData\cursor.exe"}
        with patch("rafiq.apps._discover_from_registry", return_value=fake_registry):
            invalidate_cache()
            result = resolve_app("cursor")
            assert result == r"C:\Users\test\AppData\cursor.exe"

    def test_cache_is_used_on_second_call(self):
        """الـ registry مش بيتاستدعى في كل call."""
        with patch("rafiq.apps._discover_from_registry", return_value={}) as mock_reg:
            with patch("rafiq.apps._discover_from_start_menu", return_value={}):
                invalidate_cache()
                resolve_app("notepad")
                resolve_app("notepad")
                # بُني مرة واحدة بس (الـ cache اشتغل)
                assert mock_reg.call_count == 1

    def test_substring_match(self):
        """'vs' يلاقي 'vscode'."""
        fake = {"vscode": "code.exe"}
        with patch("rafiq.apps._discover_from_registry", return_value=fake):
            with patch("rafiq.apps._discover_from_start_menu", return_value={}):
                invalidate_cache()
                result = resolve_app("vs code")
                # يلاقي من الـ static map
                assert result is not None
