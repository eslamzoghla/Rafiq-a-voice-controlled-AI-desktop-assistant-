"""
rafiq/i18n.py
=============
International language support (Arabic & English).
Manages all UI strings and system prompts in both languages.
"""

# ── Language Codes ────────────────────────────────────────────
SUPPORTED_LANGUAGES = {"ar", "en"}
DEFAULT_LANGUAGE = "ar"

# ══════════════════════════════════════════════════════════════
#  UI Strings (Interface Messages)
# ══════════════════════════════════════════════════════════════

UI_STRINGS = {
    "banner_title": {
        "ar": "رفيق v2.0 — مساعدك الذكي المطوّر",
        "en": "Rafiq v2.0 — Advanced AI Assistant",
    },
    "user_label": {
        "ar": "المستخدم",
        "en": "User",
    },
    "sessions_label": {
        "ar": "الجلسات",
        "en": "Sessions",
    },
    "last_seen_label": {
        "ar": "آخر زيارة",
        "en": "Last Seen",
    },
    "examples": {
        "ar": "أمثلة: افتح جوجل | طقس القاهرة | أخبار اليوم",
        "en": "Examples: open Google | weather Cairo | latest news",
    },
    "exit_instruction": {
        "ar": "اكتب 'خروج' للإنهاء",
        "en": "Type 'exit' to quit",
    },
    "api_key_warning": {
        "ar": "⚠️  لم يتم إعداد مفتاح API!",
        "en": "⚠️  API key not configured!",
    },
    "api_key_instruction": {
        "ar": "عيّن متغير البيئة:",
        "en": "Set environment variable:",
    },
    "welcome": {
        "ar": "مرحباً {name}! كيف يمكنني مساعدتك؟",
        "en": "Hello {name}! How can I help you?",
    },
    "listening": {
        "ar": "🎤 استمع...",
        "en": "🎤 Listening...",
    },
    "processing": {
        "ar": "⏳ معالجة الطلب...",
        "en": "⏳ Processing...",
    },
    "error_app_not_found": {
        "ar": "لم أجد برنامج '{app}' على جهازك يا {user}. تأكد إنه مثبت أو قل الاسم الإنجليزي.",
        "en": "I couldn't find app '{app}' on your system, {user}. Make sure it's installed or use the English name.",
    },
    "error_open_app": {
        "ar": "تعذّر فتح {app}: {error}",
        "en": "Failed to open {app}: {error}",
    },
    "error_open_url": {
        "ar": "تعذّر فتح الرابط: {error}",
        "en": "Failed to open URL: {error}",
    },
    "url_opened": {
        "ar": "تم فتح {url}.",
        "en": "Opened {url}.",
    },
    "app_opened": {
        "ar": "تم فتح {app}.",
        "en": "Opened {app}.",
    },
    "searching_google": {
        "ar": "جارٍ البحث عن '{query}' في جوجل.",
        "en": "Searching Google for '{query}'.",
    },
    "searching_youtube": {
        "ar": "جارٍ البحث عن '{query}' في يوتيوب.",
        "en": "Searching YouTube for '{query}'.",
    },
    "weather_loading": {
        "ar": "جارٍ جلب معلومات الطقس...",
        "en": "Fetching weather information...",
    },
    "news_loading": {
        "ar": "جارٍ جلب الأخبار...",
        "en": "Fetching news...",
    },
    "file_created": {
        "ar": "تم إنشاء الملف: {path}",
        "en": "File created: {path}",
    },
    "file_deleted": {
        "ar": "تم حذف الملف: {path}",
        "en": "File deleted: {path}",
    },
}

# ══════════════════════════════════════════════════════════════
#  System Prompts
# ══════════════════════════════════════════════════════════════

SYSTEM_PROMPTS = {
    "ar": """أنت رفيق، مساعد ذكاء اصطناعي متطور يعمل على Windows.
اسم المستخدم: {user_name}. {city_hint}
جلسات سابقة: {total_sessions}.

ردودك يجب أن تكون بالتنسيق التالي — كل أمر في سطر مستقل:
ACTION: <النوع>|<التفاصيل>
CHAT|<الرد الصوتي>

الأوامر المتاحة:
OPEN_URL|<رابط>            ← فتح موقع
SEARCH_GOOGLE|<نص>         ← بحث جوجل
SEARCH_YOUTUBE|<نص>        ← بحث يوتيوب
OPEN_APP|<اسم>             ← فتح برنامج
TYPE_TEXT|<نص>             ← كتابة نص
PRESS_KEY|<مفتاح>          ← ضغط مفتاح (مثل: enter, ctrl+c)
RUN_CMD|<أمر>              ← تشغيل أمر CMD آمن
SCREENSHOT|describe        ← التقاط الشاشة ووصفها
SCREENSHOT|save            ← حفظ لقطة شاشة فقط
FILE_CREATE|<مسار>|<محتوى> ← إنشاء ملف
FILE_READ|<مسار>           ← قراءة ملف
FILE_DELETE|<مسار>         ← حذف ملف
FILE_LIST|<مجلد>           ← عرض محتويات مجلد
WEATHER|<مدينة>            ← طقس المدينة
NEWS|<موضوع>               ← أحدث أخبار
REMEMBER|<مفتاح>|<قيمة>   ← حفظ معلومة في الذاكرة

قواعد صارمة:
1. أجب بالعربية دائماً في CHAT.
2. نفّذ الأوامر مباشرة بلا أسئلة زائدة.
3. للمهام المعقدة: استخدم عدة ACTION متتالية ثم CHAT واحد.
4. كن موجزاً ومفيداً.
5. CHAT مطلوب دائماً في النهاية (جملة قصيرة).""",
    
    "en": """You are Rafiq, an advanced AI assistant running on Windows.
User name: {user_name}. {city_hint}
Previous sessions: {total_sessions}.

Your responses must follow this format — each command on a separate line:
ACTION: <Type>|<Details>
CHAT|<Voice Response>

Available commands:
OPEN_URL|<URL>            ← Open website
SEARCH_GOOGLE|<text>      ← Google search
SEARCH_YOUTUBE|<text>     ← YouTube search
OPEN_APP|<name>           ← Open application
TYPE_TEXT|<text>          ← Type text
PRESS_KEY|<key>           ← Press key (e.g.: enter, ctrl+c)
RUN_CMD|<command>         ← Run safe CMD command
SCREENSHOT|describe       ← Take and describe screenshot
SCREENSHOT|save           ← Save screenshot only
FILE_CREATE|<path>|<content> ← Create file
FILE_READ|<path>          ← Read file
FILE_DELETE|<path>        ← Delete file
FILE_LIST|<folder>        ← List folder contents
WEATHER|<city>            ← Get city weather
NEWS|<topic>              ← Get latest news
REMEMBER|<key>|<value>    ← Save info to memory

Strict rules:
1. Respond in English for CHAT messages.
2. Execute commands directly without extra questions.
3. For complex tasks: use multiple ACTIONs then one CHAT.
4. Be concise and helpful.
5. CHAT is required at the end (short sentence).""",
}

# ══════════════════════════════════════════════════════════════
#  Helper Functions
# ══════════════════════════════════════════════════════════════

def get_string(key: str, language: str = DEFAULT_LANGUAGE, **kwargs) -> str:
    """
    Get a translated UI string.
    
    Args:
        key: String key from UI_STRINGS
        language: Language code ('ar' or 'en')
        **kwargs: Format variables (e.g., name="John")
    
    Returns:
        Translated string with variables substituted
    """
    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE
    
    if key not in UI_STRINGS:
        return key  # Fallback: return key if not found
    
    text = UI_STRINGS[key].get(language, UI_STRINGS[key].get(DEFAULT_LANGUAGE, key))
    
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass  # Silently ignore missing format keys
    
    return text


def get_system_prompt(language: str = DEFAULT_LANGUAGE, **kwargs) -> str:
    """
    Get system prompt in specified language.
    
    Args:
        language: Language code ('ar' or 'en')
        **kwargs: Format variables (user_name, city, etc.)
    
    Returns:
        System prompt with variables substituted
    """
    if language not in SUPPORTED_LANGUAGES:
        language = DEFAULT_LANGUAGE
    
    prompt = SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS[DEFAULT_LANGUAGE])
    
    if kwargs:
        # Handle city_hint specially
        if "city" in kwargs and kwargs["city"]:
            kwargs.setdefault("city_hint", f"مدينة المستخدم: {kwargs['city']}." if language == "ar" else f"User city: {kwargs['city']}.")
        else:
            kwargs.setdefault("city_hint", "")
        
        try:
            prompt = prompt.format(**kwargs)
        except KeyError:
            pass
    
    return prompt.strip()


def detect_language(text: str) -> str:
    """
    Detect language from text (simple heuristic).
    Returns 'ar' for Arabic, 'en' for English, or DEFAULT_LANGUAGE.
    """
    if not text:
        return DEFAULT_LANGUAGE
    
    # Count Arabic characters
    arabic_count = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    total_chars = len([c for c in text if c.isalpha()])
    
    if total_chars == 0:
        return DEFAULT_LANGUAGE
    
    # If more than 30% Arabic characters, consider it Arabic
    if arabic_count / total_chars > 0.3:
        return "ar"
    
    return "en"
