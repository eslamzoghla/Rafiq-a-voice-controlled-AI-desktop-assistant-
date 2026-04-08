"""
main.py
=======
نقطة الدخول الوحيدة لرفيق.
Single entry point for Rafiq.
الحلقة الرئيسية نظيفة — كل الـ logic في الـ modules.
Main loop is clean — all logic in modules.
"""

import sys

from rafiq.actions  import parse_and_execute
from rafiq.config   import EXIT_WORDS, OPENROUTER_API_KEY, PREFERRED_LANGUAGE, AUTO_DETECT_LANGUAGE
from rafiq.i18n     import get_string, detect_language, DEFAULT_LANGUAGE
from rafiq.llm      import RafiqSession
from rafiq.logger   import log
from rafiq.memory   import load_memory, save_memory, update_session_stats
from rafiq.stt      import listen
from rafiq.tts      import speak


# ══════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════

def _check_api_key() -> bool:
    if not OPENROUTER_API_KEY or "PASTE" in OPENROUTER_API_KEY:
        print("=" * 56)
        print(get_string("api_key_warning", PREFERRED_LANGUAGE))
        print(f"   {get_string('api_key_instruction', PREFERRED_LANGUAGE)}")
        print("   set OPENROUTER_API_KEY=sk-or-v1-...")
        print("=" * 56)
        return False
    return True


def _print_banner(mem: dict, lang: str = PREFERRED_LANGUAGE) -> None:
    name       = mem["user_name"]
    sessions   = mem["total_sessions"]
    last       = mem.get("last_seen", "")
    user_label = get_string("user_label", lang)
    sess_label = get_string("sessions_label", lang)
    last_label = get_string("last_seen_label", lang)
    title      = get_string("banner_title", lang)
    examples   = get_string("examples", lang)
    exit_inst  = get_string("exit_instruction", lang)

    print()
    print("╔══════════════════════════════════════════════════╗")
    print(f"║  {title:47}║")
    print("╠══════════════════════════════════════════════════╣")
    print(f"║  {user_label:11}: {name:<33}║")
    print(f"║  {sess_label:11}: {sessions:<33}║")
    if last:
        print(f"║  {last_label:11}: {last:<33}║")
    print("╠══════════════════════════════════════════════════╣")
    print(f"║  {examples:47}║")
    print(f"║  {exit_inst:47}║")
    print("╚══════════════════════════════════════════════════╝")
    print()


def _shutdown(session: RafiqSession, lang: str = PREFERRED_LANGUAGE) -> None:
    """Exit point — always executed on shutdown."""
    if lang == "ar":
        speak(f"إلى اللقاء يا {session.user_name}! سأكون هنا عند عودتك.")
        print("👋 تم إنهاء رفيق.")
    else:
        speak(f"Goodbye {session.user_name}! I'll be here when you return.")
        print("👋 Rafiq has been closed.")
    save_memory(session.memory)
    log("SYSTEM", "session ended")


# ══════════════════════════════════════════════════════════════
#  Main Loop
# ══════════════════════════════════════════════════════════════

def main() -> None:
    if not _check_api_key():
        sys.exit(1)

    # ── Initialize Session ─────────────────────────────────────
    memory  = load_memory()
    memory  = update_session_stats(memory)
    save_memory(memory)

    session = RafiqSession(memory=memory)
    
    # ── Determine Language ─────────────────────────────────────
    # Priority: 1) Memory setting, 2) Config preference, 3) Default
    current_language = memory.get("language", PREFERRED_LANGUAGE)
    if current_language not in ["ar", "en"]:
        current_language = PREFERRED_LANGUAGE
    
    _print_banner(memory, current_language)

    # ── Greeting ───────────────────────────────────────────────
    if session.user_name != "سيدي" and session.user_name != "User" and memory["total_sessions"] > 1:
        if current_language == "ar":
            speak(f"أهلاً بعودتك يا {session.user_name}! كيف أساعدك اليوم؟")
        else:
            speak(f"Welcome back, {session.user_name}! How can I help today?")
    else:
        if current_language == "ar":
            speak("مرحباً! أنا رفيق مساعدك الذكي. كيف أساعدك؟")
        else:
            speak("Hello! I'm Rafiq, your smart assistant. How can I help?")

    # ── Main Loop ──────────────────────────────────────────────
    while True:
        try:
            print("─" * 50)
            if current_language == "ar":
                print("🎙️  رفيق يستمع — قل الأمر بصوتك.")
            else:
                print("🎙️  Rafiq is listening — say your command.")
            
            user_input = listen()

            if not user_input:
                continue

            # ── Detect and Switch Language (if enabled) ────────────
            if AUTO_DETECT_LANGUAGE:
                detected_lang = detect_language(user_input)
                if detected_lang != current_language:
                    current_language = detected_lang
                    memory["language"] = current_language
                    save_memory(memory)

            # ── Check for Exit Words ───────────────────────────────
            if user_input.lower().strip() in EXIT_WORDS:
                _shutdown(session, current_language)
                break

            if current_language == "ar":
                print(f"\n🎤 أنت: {user_input}")
            else:
                print(f"\n🎤 You: {user_input}")
            log("USER", user_input)

            # ── First Message — Ask for Name if Needed ─────────────
            if session.first_message:
                session.first_message = False
                greetings_ar = {"مرحبا", "السلام", "صباح", "مساء", "أهلا", "هاي"}
                greetings_en = {"hello", "hi", "hey", "greetings"}
                
                if any(g in user_input.lower() for g in greetings_ar.union(greetings_en)):
                    greeting_reply = session.greet_new_user()
                    if greeting_reply:
                        spoken = parse_and_execute(
                            greeting_reply, session.memory
                        )
                        speak(spoken)
                        continue

            # ── Ask LLM and Execute Commands ───────────────────────
            llm_response = session.ask(user_input)
            spoken_text  = parse_and_execute(
                llm_response, session.memory, session._client
            )
            if spoken_text:
                speak(spoken_text)

        except KeyboardInterrupt:
            print("\n")
            _shutdown(session, current_language)
            break
        except Exception as e:
            lang = current_language
            if lang == "ar":
                print(f"⚠️  خطأ غير متوقع: {e}")
                speak(f"حدث خطأ غير متوقع يا {session.user_name}، أحاول مرة أخرى.")
            else:
                print(f"⚠️  Unexpected error: {e}")
                speak(f"An unexpected error occurred, {session.user_name}. Let me try again.")


if __name__ == "__main__":
    main()
