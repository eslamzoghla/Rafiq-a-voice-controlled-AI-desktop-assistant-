"""
tests/test_actions.py
=====================
Unit tests لـ:
  - execute_action (كل action type)
  - parse_and_execute (edge cases)
  - Security: CMD allowlist
"""

from unittest.mock import MagicMock, patch

import pytest

from rafiq.actions import _is_error, execute_action, parse_and_execute
from rafiq.config  import SAFE_CMD_ALLOWLIST


# ══════════════════════════════════════════════════════════════
#  Shared fixture
# ══════════════════════════════════════════════════════════════

@pytest.fixture
def mem():
    return {
        "user_name": "أحمد",
        "city":      "القاهرة",
        "preferences": {},
        "total_sessions": 1,
        "last_seen": "",
    }


# ══════════════════════════════════════════════════════════════
#  OPEN_URL
# ══════════════════════════════════════════════════════════════

class TestOpenUrl:

    def test_adds_https_when_missing(self, mem):
        with patch("webbrowser.open") as mock_open:
            result, speak = execute_action("OPEN_URL", "google.com", mem)
            mock_open.assert_called_once_with("https://google.com")
            assert "google.com" in result

    def test_preserves_existing_https(self, mem):
        with patch("webbrowser.open") as mock_open:
            execute_action("OPEN_URL", "https://example.com", mem)
            mock_open.assert_called_once_with("https://example.com")

    def test_returns_should_not_speak_on_success(self, mem):
        with patch("webbrowser.open"):
            _, should_speak = execute_action("OPEN_URL", "google.com", mem)
            assert should_speak is False

    def test_returns_should_speak_on_error(self, mem):
        with patch("webbrowser.open", side_effect=Exception("blocked")):
            result, should_speak = execute_action("OPEN_URL", "google.com", mem)
            assert should_speak is True
            assert "تعذّر" in result


# ══════════════════════════════════════════════════════════════
#  OPEN_APP
# ══════════════════════════════════════════════════════════════

class TestOpenApp:

    def test_unknown_app_returns_error_message(self, mem):
        with patch("rafiq.actions.resolve_app", return_value=None):
            result, should_speak = execute_action("OPEN_APP", "برنامج_غير_موجود", mem)
            assert should_speak is True
            assert "لم أجد" in result
            assert "أحمد" in result   # اسم المستخدم في الرسالة

    def test_known_app_opens_successfully(self, mem):
        with patch("rafiq.actions.resolve_app", return_value="notepad"):
            with patch("subprocess.Popen") as mock_popen:
                result, should_speak = execute_action("OPEN_APP", "notepad", mem)
                mock_popen.assert_called()
                assert should_speak is False

    def test_http_app_opens_browser(self, mem):
        with patch("rafiq.actions.resolve_app", return_value="https://web.whatsapp.com"):
            with patch("webbrowser.open") as mock_open:
                execute_action("OPEN_APP", "واتساب", mem)
                mock_open.assert_called_once_with("https://web.whatsapp.com")


# ══════════════════════════════════════════════════════════════
#  RUN_CMD — Security (Allowlist)
# ══════════════════════════════════════════════════════════════

DANGEROUS_COMMANDS = [
    "del file.txt",
    "DEL file.txt",           # uppercase
    "del/file.txt",           # بدون space
    "erase file.txt",
    "format c:",
    "shutdown /s",
    "rmdir /s /q C:\\",
    "powershell rm -rf ~",
    "cmd /c del important.txt",
    "rd /s /q C:\\Windows",
    "mklink /d C:\\evil C:\\Windows",
    ":(){:|:&};:",            # fork bomb
    "drop table users",
]

SAFE_COMMANDS = [
    "ping google.com",
    "ipconfig",
    "dir",
    "echo hello",
    "ver",
    "whoami",
    "tasklist",
    "systeminfo",
    "hostname",
]


class TestRunCmdSecurity:

    @pytest.mark.parametrize("cmd", DANGEROUS_COMMANDS)
    def test_dangerous_commands_are_blocked(self, cmd, mem):
        result, should_speak = execute_action("RUN_CMD", cmd, mem)
        assert should_speak is True
        assert "غير مسموح" in result, (
            f"الأمر الخطير '{cmd}' لم يُحجب!"
        )

    @pytest.mark.parametrize("cmd", SAFE_COMMANDS)
    def test_safe_commands_are_allowed(self, cmd, mem):
        mock_result = MagicMock()
        mock_result.stdout = "output"
        mock_result.stderr = ""
        with patch("subprocess.run", return_value=mock_result):
            result, _ = execute_action("RUN_CMD", cmd, mem)
            assert "غير مسموح" not in result

    def test_empty_command_is_blocked(self, mem):
        result, should_speak = execute_action("RUN_CMD", "", mem)
        assert should_speak is True
        assert "غير مسموح" in result

    def test_timeout_returns_arabic_message(self, mem):
        import subprocess
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("ping", 10)):
            result, _ = execute_action("RUN_CMD", "ping google.com", mem)
            assert "مهلة" in result

    def test_all_safe_cmds_in_allowlist_are_actually_safe(self, mem):
        """تأكد إن كل الأوامر في SAFE_CMD_ALLOWLIST مقبولة."""
        for cmd in SAFE_CMD_ALLOWLIST:
            mock_result = MagicMock(stdout="", stderr="")
            with patch("subprocess.run", return_value=mock_result):
                result, _ = execute_action("RUN_CMD", cmd, mem)
                assert "غير مسموح" not in result, f"'{cmd}' مفروض يكون آمن!"


# ══════════════════════════════════════════════════════════════
#  FILE actions
# ══════════════════════════════════════════════════════════════

class TestFileActions:

    def test_file_create_and_read(self, tmp_path, mem):
        test_file = str(tmp_path / "test.txt")
        r, _ = execute_action("FILE_CREATE", f"{test_file}|مرحبا", mem)
        assert "تم إنشاء" in r

        r2, speak = execute_action("FILE_READ", test_file, mem)
        assert "مرحبا" in r2
        assert speak is True

    def test_file_delete_missing(self, mem):
        result, should_speak = execute_action("FILE_DELETE", "/nonexistent/file.txt", mem)
        assert "غير موجود" in result
        assert should_speak is True

    def test_file_create_bad_format(self, mem):
        result, should_speak = execute_action("FILE_CREATE", "/some/path", mem)
        assert "تنسيق خاطئ" in result
        assert should_speak is True

    def test_file_list_missing_dir(self, mem):
        result, _ = execute_action("FILE_LIST", "/nonexistent/dir", mem)
        assert "غير موجود" in result

    def test_file_list_existing_dir(self, tmp_path, mem):
        (tmp_path / "a.txt").write_text("x")
        (tmp_path / "b.txt").write_text("y")
        result, _ = execute_action("FILE_LIST", str(tmp_path), mem)
        assert "a.txt" in result
        assert "b.txt" in result


# ══════════════════════════════════════════════════════════════
#  REMEMBER
# ══════════════════════════════════════════════════════════════

class TestRememberAction:

    def test_remember_city(self, tmp_path, mem, monkeypatch):
        monkeypatch.setattr("rafiq.memory.MEMORY_FILE", tmp_path / "mem.json")
        result, _ = execute_action("REMEMBER", "city|الإسكندرية", mem)
        assert "city" in result
        assert mem["city"] == "الإسكندرية"

    def test_remember_bad_format(self, mem):
        result, should_speak = execute_action("REMEMBER", "no_pipe_here", mem)
        assert "تنسيق خاطئ" in result
        assert should_speak is True


# ══════════════════════════════════════════════════════════════
#  CHAT action
# ══════════════════════════════════════════════════════════════

class TestChatAction:

    def test_chat_returns_text_and_speaks(self, mem):
        result, should_speak = execute_action("CHAT", "أهلاً بك!", mem)
        assert result == "أهلاً بك!"
        assert should_speak is True


# ══════════════════════════════════════════════════════════════
#  Unknown action
# ══════════════════════════════════════════════════════════════

class TestUnknownAction:

    def test_unknown_action_returns_error(self, mem):
        result, should_speak = execute_action("NONEXISTENT_ACTION", "details", mem)
        assert "غير معروف" in result
        assert should_speak is True


# ══════════════════════════════════════════════════════════════
#  parse_and_execute — edge cases
# ══════════════════════════════════════════════════════════════

class TestParseAndExecute:

    @pytest.fixture
    def base_mem(self):
        return {"user_name": "مريم", "city": "", "preferences": {}, "total_sessions": 1}

    def test_empty_response_returns_fallback(self, base_mem):
        result = parse_and_execute("", base_mem)
        assert result   # مش فاضي
        assert "مريم" in result

    def test_simple_chat_line(self, base_mem):
        result = parse_and_execute("CHAT|أهلاً", base_mem)
        assert "أهلاً" in result

    def test_action_with_chat(self, base_mem):
        with patch("webbrowser.open"):
            result = parse_and_execute(
                "ACTION: OPEN_URL|google.com\nCHAT|تم فتح جوجل",
                base_mem,
            )
        assert "تم فتح جوجل" in result

    def test_action_without_action_prefix(self, base_mem):
        """بعض النماذج بتبعت ACTION بدون 'ACTION:' """
        result = parse_and_execute("CHAT|مرحبا", base_mem)
        assert "مرحبا" in result

    def test_action_with_empty_details(self, base_mem):
        """OPEN_URL بدون URL."""
        with patch("webbrowser.open"):
            result = parse_and_execute("ACTION: OPEN_URL|", base_mem)
        assert result   # مش crash

    def test_action_without_pipe(self, base_mem):
        """payload بدون | → تنسيق خاطئ."""
        result = parse_and_execute("ACTION: OPEN_URL", base_mem)
        assert "تنسيق خاطئ" in result

    def test_error_from_action_appears_in_output(self, base_mem):
        """لو action رجعت error — لازم تظهر للمستخدم."""
        with patch("rafiq.actions.resolve_app", return_value=None):
            result = parse_and_execute(
                "ACTION: OPEN_APP|برنامج_غير_موجود\nCHAT|تم",
                base_mem,
            )
        assert "لم أجد" in result   # error ظهرت

    def test_multiple_actions_all_execute(self, base_mem):
        with patch("webbrowser.open") as mock_open:
            parse_and_execute(
                "ACTION: SEARCH_GOOGLE|بايثون\nACTION: SEARCH_YOUTUBE|بايثون",
                base_mem,
            )
        assert mock_open.call_count == 2

    def test_plain_text_line_added_to_output(self, base_mem):
        result = parse_and_execute("جملة عادية بدون أوامر", base_mem)
        assert "جملة عادية" in result


# ══════════════════════════════════════════════════════════════
#  _is_error helper
# ══════════════════════════════════════════════════════════════

class TestIsError:

    @pytest.mark.parametrize("text,expected", [
        ("تعذّر فتح الملف", True),
        ("خطأ في التنفيذ",   True),
        ("الملف غير موجود",  True),
        ("غير مسموح به",     True),
        ("تم فتح البرنامج",  False),
        ("أهلاً بك",          False),
        ("",                  False),
    ])
    def test_is_error_detection(self, text, expected):
        assert _is_error(text) is expected
