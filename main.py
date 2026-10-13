import asyncio
import logging
import os
import threading
import webbrowser

import edge_tts
import pygame
import requests
import speech_recognition as sr
from dotenv import load_dotenv
from openai import OpenAI  

import musicLibrary
from timers import TimerManager, handle_timer_command

# setup
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("jarvis")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

MODEL = os.getenv("AI_MODEL", "llama-3.3-70b-versatile")


VOICE = os.getenv("JARVIS_VOICE", "en-GB-RyanNeural")
VOICE_RATE = "-5%"    
VOICE_PITCH = "-5Hz" 

if not GROQ_API_KEY:
    raise SystemExit("Missing GROQ_API_KEY. Add your key to the .env file.")

client = OpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")

WAKE_WORD = "jarvis"
SYSTEM_PROMPT = (
    "You are Jarvis, a polite, witty and highly capable British AI butler, like the "
    "assistant from Iron Man. Address the user as 'sir' occasionally. "
    "Give short responses, one to three sentences."
)
MAX_HISTORY = 10  # remembers the last 10 messages (5 back-and-forth turns)
EXIT_PHRASES = {"stop", "exit", "quit", "goodbye", "go to sleep", "shut down", "turn off"}

SITES = {
    "google": "https://google.com",
    "youtube": "https://youtube.com",
    "facebook": "https://facebook.com",
    "instagram": "https://instagram.com",
    "linkedin": "https://linkedin.com",
}

TEMP_AUDIO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp.mp3")
_speak_lock = threading.Lock()  
history = []


# speech
def speak(text):
    print(f"Jarvis: {text}")
    with _speak_lock:
        try:
            asyncio.run(
                edge_tts.Communicate(text, VOICE, rate=VOICE_RATE, pitch=VOICE_PITCH).save(TEMP_AUDIO)
            )
            pygame.mixer.init()
            pygame.mixer.music.load(TEMP_AUDIO)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            pygame.mixer.music.unload()
        except Exception:
            log.exception("Speech failed")
        finally:
            if pygame.mixer.get_init():
                pygame.mixer.quit()
            if os.path.exists(TEMP_AUDIO):
                try:
                    os.remove(TEMP_AUDIO)
                except OSError:
                    pass


timers = TimerManager(speak)


# AI
def ai_process(command):
    history.append({"role": "user", "content": command})
    del history[:-MAX_HISTORY]

    try:
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}, *history],
        )
        reply = completion.choices[0].message.content
    except Exception:
        log.exception("AI request failed")
        history.pop()
        return "Sorry sir, I couldn't reach my brain right now."

    history.append({"role": "assistant", "content": reply})
    return reply


# news
def read_news():
    if not NEWS_API_KEY:
        speak("News isn't set up yet. Add your NEWS_API_KEY to the dot env file.")
        return

    try:
        response = requests.get(
            "https://newsapi.org/v2/top-headlines",
            params={"country": "us", "apiKey": NEWS_API_KEY},
            timeout=10,
        )
        response.raise_for_status()
    except requests.RequestException:
        log.exception("News request failed")
        speak("Sorry, I couldn't fetch the news.")
        return

    articles = response.json().get("articles", [])[:5]  # top 5 only
    if not articles:
        speak("I couldn't find any headlines right now.")
        return

    speak("Here are the top headlines.")
    for article in articles:
        speak(article["title"])


# commands
def process_command(command):
    """Handle one command. Returns False when Jarvis should shut down."""
    c = command.lower().strip()

    # Shut down
    if c in EXIT_PHRASES:
        timers.cancel_all()
        speak("Goodbye sir.")
        return False

    # Timers and reminders
    reply = handle_timer_command(c, timers)
    if reply:
        speak(reply)
        return True

    # Open websites
    for name, url in SITES.items():
        if f"open {name}" in c:
            webbrowser.open(url)
            return True

    # Play music
    if c.startswith("play "):
        song = c.removeprefix("play ").strip()
        link = musicLibrary.music.get(song)
        if link:
            webbrowser.open(link)
        else:
            speak(f"I couldn't find {song} in your library.")
        return True

    # News
    if c == "news" or "the news" in c or "headlines" in c:
        read_news()
        return True

    # Everything else goes to the AI
    speak(ai_process(command))
    return True


# main loop
def main():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        log.info("Calibrating for background noise...")
        recognizer.adjust_for_ambient_noise(source, duration=1)

    speak("Initializing Jarvis. All systems online.")
    running = True

    try:
        while running:
            try:
                with sr.Microphone() as source:
                    log.info("Listening for wake word...")
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=4)

                word = recognizer.recognize_google(audio)
                if WAKE_WORD not in word.lower():
                    continue

                speak("Yes sir?")

                with sr.Microphone() as source:
                    log.info("Jarvis active...")
                    audio = recognizer.listen(source, timeout=8, phrase_time_limit=15)

                command = recognizer.recognize_google(audio)
                log.info("Heard: %s", command)
                running = process_command(command)

            except sr.WaitTimeoutError:
                continue  
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                log.error("Speech service error: %s", e)
            except Exception:
                log.exception("Unexpected error")
    except KeyboardInterrupt:
        print("\nShutting down.")


if __name__ == "__main__":
    main()
