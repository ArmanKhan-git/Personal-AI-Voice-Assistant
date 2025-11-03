# 🤖 JARVIS - Advanced Voice Assistant

> A powerful, intelligent voice-controlled desktop assistant powered by Google's Gemini AI, featuring Spotify integration, YouTube control, and comprehensive system automation.


---

## 🌟 Features

### 🎵 **Spotify Control**
- Play songs, albums, and playlists by voice
- Control playback (play/pause, next, previous)
- Search and play specific tracks
- Access your liked songs playlist
- Adjust Spotify volume
- Toggle shuffle and repeat modes
- Like/save songs to your library

### 🎥 **YouTube Integration**
- Search YouTube by voice
- Play videos directly ("play X on YouTube")
- Select specific search results ("play the first video")
- Context-aware video selection

### 🌐 **Web Automation**
- Open websites with voice commands
- Context-aware searching (YouTube, Google, Amazon, Flipkart, etc.)
- Multi-platform search support
- Smart browser control

### 🖥️ **System Control**
- Open and close applications
- Take screenshots
- Adjust system volume
- Shutdown, restart, or sleep computer
- Get current time

### 🧠 **AI-Powered Conversations**
- Natural conversations powered by Google Gemini 2.5 Flash
- Context-aware responses
- Personality-driven interactions (British formal tone)
- Conversation history tracking

### 🔊 **Wake/Sleep Mode**
- Activate with wake words: "Jarvis", "Hey Jarvis", "OK Jarvis"
- Sleep mode for privacy and power saving
- Always listening in background

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** installed
- **Windows OS** (uses Windows-specific APIs)
- **Microphone** for voice input
- **Internet connection** for speech recognition and AI
- **Spotify Desktop App** (for Spotify features)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/ArmanKhan-git/Personal-AI-Voice-Assistant.git
cd Personal-AI-Voice-Assistant
```

2. **Create a virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

**⚠️ PyAudio Installation on Windows:**
If PyAudio fails to install, download the wheel file:
- Visit: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
- Download the appropriate `.whl` file for your Python version
- Install: `pip install PyAudio‑0.2.14‑cpXX‑cpXX‑win_amd64.whl`

4. **Set up environment variables**

Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

Get your Gemini API key: https://makersuite.google.com/app/apikey

5. **Run the assistant**
```bash
python assistant_custom_voice.py
```

---

## 📖 Usage Guide

### Wake/Sleep Commands

| Command | Action |
|---------|--------|
| "Jarvis", "Hey Jarvis", "OK Jarvis" | Wake up the assistant |
| "Sleep Jarvis", "Go to sleep", "Thank you Jarvis" | Put assistant to sleep |
| "Stop", "Exit", "Quit" | Completely exit the program |

### Spotify Commands

| Command | Action |
|---------|--------|
| "Play [song name] on Spotify" | Play a specific song |
| "Play liked songs" | Play your liked songs playlist |
| "Pause", "Resume" | Toggle playback |
| "Next song", "Skip" | Skip to next track |
| "Previous song" | Go to previous track |
| "Search Spotify for [query]" | Search in Spotify |
| "Spotify volume up/down" | Adjust Spotify volume |
| "Shuffle", "Repeat" | Toggle shuffle/repeat |
| "Like this song" | Save current song |

### YouTube Commands

| Command | Action |
|---------|--------|
| "Play [video name] on YouTube" | Search and play first result |
| "Search YouTube for [query]" | Search YouTube |
| "Play the first video" | Play specific search result |
| "Play the 3rd video" | Play numbered video |
| "Open YouTube" | Open YouTube homepage |

### Web & Search Commands

| Command | Action |
|---------|--------|
| "Search Google for [query]" | Google search |
| "Search Amazon for [query]" | Amazon search |
| "Search [query]" | Context-aware search |
| "Open [website]" | Open any website |
| "Open Google", "Open Instagram" | Open specific sites |

### System Commands

| Command | Action |
|---------|--------|
| "Open [app name]" | Launch application |
| "Close [app name]" | Terminate application |
| "Screenshot", "Capture screen" | Take screenshot |
| "Volume up/down" | Adjust system volume |
| "Mute" | Mute system |
| "What time is it?" | Get current time |
| "Shutdown", "Restart", "Sleep" | System power control |

### AI Conversation

Simply speak naturally to JARVIS for:
- General questions
- Information lookup
- Casual conversation
- Task assistance

---

## 🎯 Command Examples

```
User: "Hey Jarvis"
JARVIS: "Yes sir, I'm online now"

User: "Play Boyfriend by Karan Aujla on Spotify"
JARVIS: "Playing Boyfriend by Karan Aujla on Spotify"

User: "Search YouTube for Python tutorials"
JARVIS: "Here are the YouTube results for Python tutorials"

User: "Play the first video"
JARVIS: "Playing video number 1"

User: "What's the weather like?"
JARVIS: [Provides weather information via Gemini AI]

User: "Thank you Jarvis"
JARVIS: "Welcome Sir! Going to sleep mode sir. Say my name to wake me up"
```

---

## ⚙️ Configuration

### Customizing Voice

Change the voice in the code:
```python
VOICE = "en-US-GuyNeural"  # Male British-like voice
# VOICE = "en-US-AriaNeural"  # Female voice
# VOICE = "en-GB-RyanNeural"  # British male voice
```

Available voices: [Microsoft Edge TTS Voices](https://speech.microsoft.com/portal/voicegallery)

### Adjusting Wake/Sleep Words

Modify in the code:
```python
WAKE_WORDS = ["jarvis", "hey jarvis", "ok jarvis"]
SLEEP_WORDS = ["sleep jarvis", "go to sleep", "sleep mode"]
```

### Modifying AI Personality

Edit the `JARVIS_PERSONALITY` variable to customize responses.

---

## 🛠️ Troubleshooting

### Microphone Not Working
- Check Windows microphone permissions
- Verify microphone is set as default device
- Test with: `python -m speech_recognition`

### PyAudio Installation Fails
- Download precompiled wheel from [Unofficial Windows Binaries](https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio)
- Match your Python version (cp311 = Python 3.11)

### Spotify Commands Not Working
- Ensure Spotify Desktop app is installed and running
- Check if keyboard shortcuts work manually in Spotify
- Try running the script as administrator

### SetForegroundWindow Error
- This is normal on Windows and is handled gracefully
- Commands should still work even if window focusing fails

### Gemini API Errors
- Verify API key in `.env` file
- Check internet connection
- Ensure API key has proper permissions

---

## 📁 Project Structure

```
jarvis-assistant/
│
├── assistant_custom_voice.py    # Main application file
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables (create this)
├── README.md                     # This file
│
└── Pictures/
    └── JARVIS_Screenshots/       # Screenshots folder (auto-created)
```

---

## 🔒 Privacy & Security

- **Local Processing**: Speech recognition requires internet (Google Speech API)
- **AI Queries**: Sent to Google Gemini API
- **No Data Storage**: Conversation history stored in memory only
- **Environment Variables**: API keys stored in `.env` (never commit this file)
- **Wake/Sleep Mode**: Provides privacy control

---



## 🐛 Known Issues

- Windows-only (uses `pywin32` and Windows APIs)
- Spotify keyboard shortcuts may vary by region
- SetForegroundWindow occasionally fails (handled gracefully)
- Voice recognition requires clear audio environment

---


## 👨‍💻 Author

**Arman Khan**

- GitHub: [@ArmanKhan-git](https://github.com/ArmanKhan-git)
- Email: armankkhan14@gmail.com

---

## 🙏 Acknowledgments

- **Google Gemini AI** - For powerful conversational AI
- **Microsoft Edge TTS** - For natural text-to-speech
- **Spotify** - For music streaming integration
- **Python Community** - For amazing libraries

---

## 💡 Inspiration

Inspired by Tony Stark's JARVIS from the Marvel Cinematic Universe - bringing AI assistance to everyday computing.

---

## ⭐ Star History

If you find this project useful, please consider giving it a star! ⭐

---

**Made with ❤️ and Python**
