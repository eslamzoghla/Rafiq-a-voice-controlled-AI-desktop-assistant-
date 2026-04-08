<div align="center">

```
██████╗  █████╗ ███████╗██╗ ██████╗
██╔══██╗██╔══██╗██╔════╝██║██╔═══██╗
██████╔╝███████║█████╗  ██║██║   ██║
██╔══██╗██╔══██║██╔══╝  ██║██║▄▄ ██║
██║  ██║██║  ██║██║     ██║╚██████╔╝
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝ ╚══▀▀═╝
```

# رفيق · Rafiq

**An first AI desktop assistant for Windows**  
*Voice-controlled · Modular · Secure · Fully tested*

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)
[![OpenRouter](https://img.shields.io/badge/Powered%20by-OpenRouter-6366f1?style=flat-square)](https://openrouter.ai)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?style=flat-square&logo=windows&logoColor=white)](https://microsoft.com/windows)
[![Tests](https://img.shields.io/badge/Tests-53%20passing-22c55e?style=flat-square)](tests/)

[Features](#-features) · [Quick Start](#-quick-start) · [Architecture](#-architecture) · [Commands](#-commands) · [Configuration](#-configuration) · [Contributing](#-contributing)

</div>

---

## Overview

Rafiq (رفيق — Arabic for *companion*) is a voice-controlled AI desktop assistant built natively for Arabic and English speakers on Windows. You speak; Rafiq listens, understands, and acts — opening apps, searching the web, managing files, fetching weather, reading news, and more.

Unlike generic voice assistants, Rafiq is **LLM-native**: your intent is understood by a language model, not a brittle keyword matcher. Every action Rafiq takes goes through a structured command protocol, making it transparent, extensible, and safe.

```
You say:  "افتح يوتيوب وابحث عن موسيقى هادية"
Rafiq:    → Opens YouTube
          → Types the search query automatically
          → "تم البحث عن موسيقى هادية في يوتيوب"
```

---

## ✨ Features

| Category | Details |
|---|---|
| 🎙️ **Voice Input** | Arabic (EG/SA) + English, auto-retry, ambient noise calibration |
| 🔊 **Voice Output** | Azure Neural TTS (`ar-EG-SalmaNeural`), in-memory audio (no disk I/O) |
| 🧠 **AI Brain** | OpenRouter LLM with primary + fallback model chain |
| 🖥️ **App Control** | Dynamic discovery from Windows Registry + Start Menu |
| 📁 **File Manager** | Create · Read · Delete · List — with proper error reporting |
| 🌤️ **Weather** | Real-time via wttr.in — no API key needed |
| 📰 **News** | Google News RSS — any topic, in Arabic |
| 📸 **Screenshots** | Capture + optional AI description |
| 💾 **Persistent Memory** | Remembers your name, city, and preferences across sessions |
| 🔒 **Secure CMD** | Allowlist-only shell commands — blocklists are not enough |
| 🧪 **Well Tested** | 53 unit tests covering security, edge cases, and error paths |

---

## 🚀 Quick Start

### 1 — Prerequisites

- Windows 10/11
- Python 3.11+
- A microphone
- An [OpenRouter](https://openrouter.ai) API key

### 2 — Install

```bash
git clone https://github.com/eslamzoghla/Rafiq-a-voice-controlled-AI-desktop-assistant-.git
cd rafiq
pip install -r requirements.txt
```

### 3 — Configure

```bash
# Windows CMD
set OPENROUTER_API_KEY=sk-or-v1-...

# Windows PowerShell
$env:OPENROUTER_API_KEY = "sk-or-v1-..."
```

### 4 — Run

```bash
python main.py
```

Rafiq will greet you, ask for your name on first run, and start listening immediately.

### 5 — Run Tests

```bash
pytest tests/ -v
```

---

## 🏗️ Architecture

Rafiq is structured as a clean Python package — one responsibility per module, no god files, no global state.

```
rafiq/
│
├── main.py                  ← Entry point & main loop only
│
├── rafiq/
│   ├── config.py            ← All constants & settings (single source of truth)
│   ├── memory.py            ← Persistent memory: load / save / remember
│   ├── logger.py            ← Session logging to file
│   │
│   ├── llm.py               ← RafiqSession class + _call_llm()
│   ├── actions.py           ← execute_action() + parse_and_execute()
│   ├── apps.py              ← Dynamic app discovery (Registry + Start Menu)
│   ├── tools.py             ← Files, weather, news, screenshots
│   │
│   ├── stt.py               ← Speech-to-text with calibration caching
│   └── tts.py               ← Text-to-speech via BytesIO (no temp files)
│
└── tests/
    ├── test_memory.py        ← Memory edge cases (corrupt JSON, missing keys…)
    ├── test_actions.py       ← Actions + parser + security test suite
    └── test_apps.py          ← App discovery & cache behavior
```

### Key Design Decisions

**`RafiqSession` over globals** — All conversation state (history, memory, first-message flag) lives inside a session object. This makes the code testable and eliminates hidden shared state.

**`_call_llm()` is isolated** — The raw LLM call is a single function that returns `str | None`. It can be mocked in one line in any test.

**Allowlist, not blocklist** — `RUN_CMD` only permits commands explicitly listed in `SAFE_CMD_ALLOWLIST`. Anything not on the list is denied by default — including obfuscated variants like `DEL`, `del/file`, and nested shell calls.

**Error visibility** — Every `execute_action()` returns `(result, should_speak)`. Errors always bubble up to the user — they are never silently swallowed.

**No disk I/O for TTS** — Audio is streamed into a `BytesIO` buffer and played directly by pygame, skipping the write-read-delete cycle on every utterance.

---

## 🗣️ Commands

Rafiq understands natural Arabic. These are the underlying actions the LLM maps your words to:

| Action | Syntax | Example trigger |
|---|---|---|
| `OPEN_URL` | `OPEN_URL\|<url>` | "افتح موقع جيثب" |
| `SEARCH_GOOGLE` | `SEARCH_GOOGLE\|<query>` | "ابحث عن بايثون" |
| `SEARCH_YOUTUBE` | `SEARCH_YOUTUBE\|<query>` | "دور على موسيقى كلاسيكية" |
| `OPEN_APP` | `OPEN_APP\|<name>` | "افتح الفيجوال ستوديو" |
| `TYPE_TEXT` | `TYPE_TEXT\|<text>` | "اكتب مرحبا في المفكرة" |
| `PRESS_KEY` | `PRESS_KEY\|<key>` | "اضغط كنترول سي" |
| `RUN_CMD` | `RUN_CMD\|<cmd>` | "اعرض الاي بي" |
| `SCREENSHOT` | `SCREENSHOT\|save` or `describe` | "التقط لقطة شاشة وصفها" |
| `FILE_CREATE` | `FILE_CREATE\|<path>\|<content>` | "أنشئ ملف notes.txt" |
| `FILE_READ` | `FILE_READ\|<path>` | "اقرأ ملف التقرير" |
| `FILE_DELETE` | `FILE_DELETE\|<path>` | "احذف الملف القديم" |
| `FILE_LIST` | `FILE_LIST\|<dir>` | "اعرض محتويات المستندات" |
| `WEATHER` | `WEATHER\|<city>` | "ما الطقس في القاهرة؟" |
| `NEWS` | `NEWS\|<topic>` | "أخبار التكنولوجيا" |
| `REMEMBER` | `REMEMBER\|<key>\|<value>` | "تذكر إن مدينتي الإسكندرية" |

The LLM can chain multiple actions in a single response for complex requests.

---

## ⚙️ Configuration

All settings are in `rafiq/config.py` — edit once, applies everywhere.

```python
# Models
PRIMARY_MODEL  = "openai/gpt-4o-mini"     # Main model
FALLBACK_MODEL = "openai/gpt-3.5-turbo"   # Used if primary fails
VISION_MODEL   = "openai/gpt-4o-mini"     # For screenshot descriptions

# Voice
TTS_VOICE    = "ar-EG-SalmaNeural"        # Azure Neural voice
TTS_RATE     = "+5%"                       # Speech rate
TTS_MAX_CHARS = 400                        # Max chars per utterance

# STT
STT_CALIBRATION_TTL = 300                  # Re-calibrate every 5 min (seconds)
STT_TIMEOUT         = 8                    # Listen timeout (seconds)

# Conversation
MAX_HISTORY = 6                            # Turns kept in context

# Security
SAFE_CMD_ALLOWLIST = frozenset({           # Only these CMD commands are allowed
    "ipconfig", "ping", "dir", "echo",
    "systeminfo", "tasklist", "ver", ...
})
```

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENROUTER_API_KEY` | ✅ Yes | Your OpenRouter API key |
| `OPENAI_API_KEY` | Optional | Enables Whisper STT fallback |

---

## 🔒 Security

### CMD Execution

Rafiq uses an **allowlist** approach for shell command execution — the only safe design:

```python
# ✅ Allowed — explicitly listed
"ping google.com"   →  executes
"ipconfig"          →  executes

# ❌ Blocked — anything not on the allowlist
"del file.txt"      →  "هذا الأمر غير مسموح به"
"DEL file.txt"      →  blocked  (case-insensitive)
"del/file.txt"      →  blocked  (no-space variant)
"format c:"         →  blocked
"powershell rm -rf" →  blocked
```

### What Rafiq Does Not Do

- Does not execute arbitrary code from LLM responses
- Does not access files outside of explicit user requests
- Does not store API keys in code (environment variables only)
- Does not make network requests except: OpenRouter API, wttr.in, Google News RSS, and URLs you explicitly request

---

## 🧪 Tests

```
tests/
├── test_memory.py    — 15 tests
│   Load with missing file · corrupt JSON · empty file · missing keys
│   Save with Arabic content · atomic write · reload consistency
│   remember() for name / city / custom preferences
│
├── test_actions.py   — 30+ tests
│   Security: 10 dangerous commands blocked · 18 safe commands allowed
│   File ops: create / read / delete / list + all error paths
│   OPEN_URL: https prepending · error bubbling · should_speak flags
│   OPEN_APP: unknown app error message · URL apps · shortcuts
│   parse_and_execute: empty · malformed · multi-action · error visibility
│
└── test_apps.py      —  8 tests
    Static map fallback · Arabic prefix stripping · case-insensitive
    Registry injection · cache hit behavior · unknown app → None
```

Run with coverage:

```bash
pytest tests/ -v --tb=short
pytest tests/ --cov=rafiq --cov-report=term-missing
```

---

## 🛠️ Extending Rafiq

### Adding a New Action

1. Add the handler in `rafiq/actions.py` inside `execute_action()`:

```python
elif action_type == "MY_ACTION":
    result = do_something(details)
    return result, True   # True = speak the result
```

2. Add it to the system prompt in `rafiq/llm.py`:

```
MY_ACTION|<details>    ← description of when to use it
```

3. Write a test in `tests/test_actions.py`.

### Adding Apps to the Static Map

Edit `STATIC_APP_MAP` in `rafiq/config.py`. The dynamic Registry discovery handles newly installed apps automatically — the static map is just a fallback and an alias layer for Arabic names.

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `openai` | OpenRouter API client |
| `edge-tts` | Azure Neural TTS (free, no key needed) |
| `pygame` | Audio playback |
| `SpeechRecognition` | Microphone input + Google STT |
| `pyautogui` | Keyboard/mouse automation (`TYPE_TEXT`, `PRESS_KEY`) |
| `pyperclip` | Clipboard access for reliable Arabic text input |

Optional: `pyautogui` + `pyperclip` are only needed for `TYPE_TEXT` and `PRESS_KEY` actions. Rafiq degrades gracefully if they are absent.

---

## 🗺️ Roadmap

- [ ] Wake word detection (`"رفيق"` activates listening)
- [ ] Plugin system for custom actions
- [ ] GUI tray icon with status indicator
- [ ] Whisper local STT (offline mode)
- [ ] Multi-language memory (remember preferred language per topic)
- [ ] Action history & undo

---

## 🤝 Contributing

Contributions are welcome. Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Write tests for your changes
4. Ensure all tests pass: `pytest tests/ -v`
5. Open a pull request with a clear description

For bug reports, please include the relevant section of `rafiq_log.txt`.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

Built with care for Arabic speakers everywhere · صُنع باهتمام للناطقين بالعربية في كل مكان

</div>
