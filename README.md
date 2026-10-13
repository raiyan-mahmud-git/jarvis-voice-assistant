# Jarvis Voice Assistant

A voice-controlled desktop assistant in Python, inspired by Jarvis from Iron Man. Say the wake word, give a command, and Jarvis answers out loud in a British male voice.

## Features

- **Wake word:** say "Jarvis" and wait for "Yes sir?"
- **Timers and reminders:** "set a timer for 5 minutes", "remind me to stretch in 10 minutes"
- **Open websites:** Google, YouTube, Facebook, Instagram, LinkedIn
- **Play music:** plays songs from a list you control in `musicLibrary.py`
- **News headlines:** reads the top 5 US headlines
- **AI answers:** anything else goes to an AI model (via Groq) and Jarvis speaks the reply
- **Conversation memory:** remembers the last few exchanges, so follow-up questions work
- **Male voice:** uses Microsoft neural voices through `edge-tts`, with no API key needed

## Requirements

- Python 3.10 or newer
- A working microphone and speakers
- An internet connection (speech recognition, text-to-speech and AI replies are online services)
- A free [Groq API key](https://console.groq.com/keys)
- A free [NewsAPI key](https://newsapi.org) (optional, only for the news command)

## Setup

1. **Clone the repo and open the folder**

   ```
   git clone https://github.com/raiyan-mahmud-git/jarvis-voice-assistant.git
   cd jarvis-voice-assistant
   ```

2. **Create and activate a virtual environment**

   ```
   python -m venv .venv
   ```

   - Windows (PowerShell): `.venv\Scripts\Activate.ps1`
   - Windows (Command Prompt): `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`

   If PowerShell blocks the script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

3. **Install the dependencies**

   ```
   pip install -r requirements.txt
   ```

   If PyAudio fails to install on Windows, try `pip install pipwin` then `pipwin install pyaudio`. On macOS, run `brew install portaudio` first.

4. **Add your keys**

   Create a file named `.env` in the project folder:

   ```
   GROQ_API_KEY=your-groq-key
   NEWS_API_KEY=your-newsapi-key
   ```

   Never commit this file. It is already listed in `.gitignore`.

5. **Run it**

   ```
   python main.py
   ```

   You can run `python client.py` first to check that your Groq key works.

## Voice commands

Say "Jarvis", wait for "Yes sir?", then say a command.

| Say | What happens |
|---|---|
| "open YouTube" | Opens the site in your browser |
| "play faded" | Opens that song from `musicLibrary.py` |
| "tell me the news" | Reads the top 5 headlines |
| "set a timer for 5 minutes" | Starts a timer (also "1 hour 30 minutes", "half an hour") |
| "remind me to drink water in 10 minutes" | Speaks a reminder when time is up |
| "how much time is left on my timer" | Lists active timers and reminders |
| "cancel all timers" | Cancels them |
| "what is the capital of France" | Sent to the AI, answered out loud |
| "goodbye" | Shuts Jarvis down (also "stop", "exit", "quit") |

Press `Ctrl+C` in the terminal to force quit.

## Configuration

Optional settings in `.env`:

| Variable | Default | Purpose |
|---|---|---|
| `AI_MODEL` | `openai/gpt-oss-20b` | The Groq model used for answers |
| `JARVIS_VOICE` | `en-GB-RyanNeural` | The voice. Others: `en-GB-ThomasNeural`, `en-US-GuyNeural`, `en-US-ChristopherNeural` |

Groq's model list changes over time. If you get a "model not found" error, check which models your key can use and update `AI_MODEL`.

To add songs, edit `musicLibrary.py` and add a line like `"song name": "https://youtube.com/watch?v=...",`.

## Project structure

```
├── main.py            # Wake word, command handling, speech, AI replies
├── timers.py          # Timer and reminder logic
├── musicLibrary.py    # Song names and links
├── client.py          # Quick test for your Groq key
├── requirements.txt   # Python dependencies
└── .gitignore         # Keeps keys and the virtual environment out of Git
```

## Troubleshooting

- **"Missing GROQ_API_KEY":** your `.env` file is missing, misnamed (check it isn't `.env.txt`), or in a different folder from `main.py`.
- **`ModuleNotFoundError`:** the virtual environment isn't active. Look for `(.venv)` at the start of your terminal prompt, then run `pip install -r requirements.txt`.
- **Jarvis doesn't hear the wake word:** speak clearly after the "Listening" message appears, and reduce background noise. Headphones help, because the microphone can pick up Jarvis's own voice.

## About this project

I wrote the first version of this assistant myself. It was then improved with help from Claude, an AI assistant made by Anthropic, which fixed bugs, added the timers and reminders, switched the voice to a male one, moved the API keys into a `.env` file, and switched the AI backend to Groq. I tested and run it myself.

## Ideas for the future

- Weather and time/date commands
- Search by voice ("search for ...")
- Opening local apps
- A local wake-word engine that works offline
