"""
rafiq/tools.py
==============
أدوات مستقلة: ملفات، طقس، أخبار، لقطة شاشة.
كل دالة ترجع string جاهز للعرض/النطق.
"""

import base64
import re
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

from .config import VISION_MODEL


# ══════════════════════════════════════════════════════════════
#  لقطة الشاشة
# ══════════════════════════════════════════════════════════════

def take_screenshot(mode: str = "save", llm_client=None) -> str:
    """
    التقاط لقطة شاشة.
    mode='save'     → حفظ على سطح المكتب فقط
    mode='describe' → حفظ + وصف بالذكاء الاصطناعي (يحتاج llm_client)
    """
    try:
        import pyautogui
    except ImportError:
        return "مكتبة pyautogui غير مثبتة. شغّل: pip install pyautogui"

    ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
    ss_path = Path.home() / "Desktop" / f"rafiq_screenshot_{ts}.png"

    try:
        time.sleep(0.5)
        img = pyautogui.screenshot()
        img.save(str(ss_path))
    except Exception as e:
        return f"تعذّر التقاط الشاشة: {e}"

    if mode == "save":
        return f"تم حفظ لقطة الشاشة: {ss_path.name}"

    # ── وصف ذكي ──────────────────────────────────────────────
    if llm_client is None:
        return f"تم حفظ اللقطة لكن لا يوجد عميل AI لوصفها: {ss_path.name}"

    try:
        with open(ss_path, "rb") as f:
            b64 = base64.standard_b64encode(f.read()).decode()

        resp = llm_client.chat.completions.create(
            model=VISION_MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/png;base64,{b64}"}},
                    {"type": "text",
                     "text": "صف ما تراه على الشاشة بالعربية في جملتين أو ثلاث."},
                ],
            }],
            max_tokens=200,
        )
        description = (resp.choices[0].message.content or "").strip()
        return description or "تم التقاط الشاشة لكن تعذّر وصفها."
    except Exception as e:
        return f"تم حفظ اللقطة لكن تعذّر وصفها: {e}"


# ══════════════════════════════════════════════════════════════
#  الملفات
# ══════════════════════════════════════════════════════════════

def file_create(path_str: str, content: str) -> str:
    try:
        p = Path(path_str).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"تم إنشاء الملف: {p}"
    except OSError as e:
        return f"تعذّر إنشاء الملف: {e}"


def file_read(path_str: str, max_chars: int = 800) -> str:
    try:
        p = Path(path_str).expanduser()
        if not p.exists():
            return f"الملف غير موجود: {p}"
        text = p.read_text(encoding="utf-8", errors="replace")
        if len(text) > max_chars:
            text = text[:max_chars] + "\n... [تم اقتصار المحتوى]"
        return text
    except OSError as e:
        return f"تعذّر قراءة الملف: {e}"


def file_delete(path_str: str) -> str:
    try:
        p = Path(path_str).expanduser()
        if not p.exists():
            return f"الملف غير موجود: {p}"
        p.unlink()
        return f"تم حذف الملف: {p}"
    except OSError as e:
        return f"تعذّر حذف الملف: {e}"


def file_list(dir_str: str = ".", max_items: int = 30) -> str:
    try:
        d = Path(dir_str).expanduser()
        if not d.exists():
            return f"المجلد غير موجود: {d}"
        items = sorted(d.iterdir())
        if not items:
            return "المجلد فارغ."
        lines = [
            f"{'📁' if item.is_dir() else '📄'} {item.name}"
            for item in items[:max_items]
        ]
        result = "\n".join(lines)
        if len(items) > max_items:
            result += f"\n... و{len(items) - max_items} عنصر آخر"
        return result
    except OSError as e:
        return f"تعذّر قراءة المجلد: {e}"


# ══════════════════════════════════════════════════════════════
#  الطقس والأخبار
# ══════════════════════════════════════════════════════════════

def get_weather(city: str, timeout: int = 6) -> str:
    """طقس المدينة عبر wttr.in — بدون مفتاح API."""
    try:
        url = f"https://wttr.in/{quote(city)}?format=3&lang=ar"
        req = urllib.request.Request(url, headers={"User-Agent": "rafiq-assistant/2.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8").strip()
    except Exception as e:
        return f"تعذّر جلب الطقس: {e}"


def get_news(topic: str, count: int = 5, timeout: int = 6) -> str:
    """أحدث أخبار عبر RSS جوجل نيوز."""
    try:
        url = (
            f"https://news.google.com/rss/search"
            f"?q={quote(topic)}&hl=ar&gl=EG&ceid=EG:ar"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "rafiq-assistant/2.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            content = r.read().decode("utf-8")

        # استخراج العناوين — نتجاهل أول عنوانين (اسم القناة والقسم)
        raw_titles = re.findall(r"<title>(.*?)</title>", content)[2 : 2 + count]
        titles = [re.sub(r"<[^>]+>", "", t).strip() for t in raw_titles]
        titles = [t for t in titles if t]   # إزالة الفارغة

        if not titles:
            return f"لا توجد أخبار حديثة عن {topic}."
        return "أحدث الأخبار:\n" + "\n".join(f"• {t}" for t in titles)
    except Exception as e:
        return f"تعذّر جلب الأخبار: {e}"
