import speech_recognition as sr
import os
import shutil
import pyautogui
from pathlib import Path
from datetime import datetime
import google.generativeai as genai
from collections import deque
from dotenv import load_dotenv
import psutil
import re
import keyboard
import time
import webbrowser
import urllib.parse
import requests
import json
import asyncio
import edge_tts
import pygame
import tempfile
import win32gui
import win32con

# ====== LOAD ENVIRONMENT VARIABLES ======
load_dotenv()

# ====== WAKE/SLEEP SYSTEM ======
WAKE_WORDS = ["jarvis", "hey jarvis", "ok jarvis"]
SLEEP_WORDS = ["sleep jarvis", "go to sleep", "sleep mode","thank you jarvis","thank u jarvis" ]
is_awake = False  # Starts in sleep mode

# ====== MEMORY ========
last_search_query = None
pending_action = None
current_context = None
spotify_query = None

# ========== CONFIG ==========
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("⚠️ GEMINI_API_KEY not found in .env file!")

genai.configure(api_key=API_KEY)
MODEL_NAME = "models/gemini-2.5-flash"
model = genai.GenerativeModel(MODEL_NAME)

# ========== EDGE-TTS SETUP ==========
TEMP_DIR = tempfile.gettempdir()
OUTPUT_PATH = os.path.join(TEMP_DIR, f"JARVIS_voice_{os.getpid()}.mp3")
VOICE = "en-GB-RyanNeural"

pygame.mixer.init()

async def generate_speech(text):
    """Generate speech using Edge-TTS"""
    try:
        if os.path.exists(OUTPUT_PATH):
            try:
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()
                time.sleep(0.2)
                os.remove(OUTPUT_PATH)
            except:
                pass
        
        communicate = edge_tts.Communicate(text, VOICE)
        await communicate.save(OUTPUT_PATH)
        time.sleep(0.2)
        
        if os.path.exists(OUTPUT_PATH) and os.path.getsize(OUTPUT_PATH) > 1000:
            return True
        
        print("⚠️ Edge-TTS file generation failed")
        return False
        
    except Exception as e:
        print(f"⚠️ Edge-TTS error: {e}")
        return False

def speak(text):
    """Speak using Edge-TTS"""
    print(f"💬 JARVIS: {text}")
    
    if not text or not text.strip():
        return
    
    try:
        if not asyncio.run(generate_speech(text)):
            return
        
        if not os.path.exists(OUTPUT_PATH) or os.path.getsize(OUTPUT_PATH) < 1000:
            print("⚠️ Audio file too small or missing")
            return
        
        pygame.mixer.music.load(OUTPUT_PATH)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        time.sleep(0.1)
        
        try:
            os.remove(OUTPUT_PATH)
        except:
            pass
            
    except Exception as e:
        print(f"⚠️ Speech error: {e}")
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            if os.path.exists(OUTPUT_PATH):
                os.remove(OUTPUT_PATH)
        except:
            pass

# ========== INITIALIZATION ==========
recognizer = sr.Recognizer()

def listen():
    """Listen for voice commands."""
    with sr.Microphone() as source:
        if not is_awake:
            print("💤 Sleeping... Say wake word to activate")
        else:
            print("🎙️ Listening...")
        
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            return ""
    
    try:
        command = recognizer.recognize_google(audio)
        print(f"🗣️ You said: {command}")
        return command.lower()
    except sr.UnknownValueError:
        return ""
    except sr.RequestError:
        if is_awake:
            speak("Speech service is unavailable.")
        return ""

# ========== SPOTIFY CONTROL FUNCTIONS ==========
def is_spotify_running():
    """Check if Spotify is running"""
    for proc in psutil.process_iter(['name']):
        try:
            if 'spotify' in proc.info['name'].lower():
                return True
        except:
            continue
    return False

def focus_spotify():
    """Bring Spotify window to foreground"""
    def callback(hwnd, windows):
        if win32gui.IsWindowVisible(hwnd):
            try:
                title = win32gui.GetWindowText(hwnd)
                if 'spotify' in title.lower():
                    windows.append(hwnd)
            except:
                pass
        return True
    
    windows = []
    win32gui.EnumWindows(callback, windows)
    
    if windows:
        hwnd = windows[0]
        try:
            # Try to restore the window if minimized
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            time.sleep(0.2)
            
            # Try multiple methods to bring window to foreground
            try:
                win32gui.SetForegroundWindow(hwnd)
            except:
                # If SetForegroundWindow fails, try alternative method
                import ctypes
                # Get the thread ID of the foreground window
                foreground_thread = ctypes.windll.user32.GetWindowThreadProcessId(
                    ctypes.windll.user32.GetForegroundWindow(), None)
                # Get the thread ID of the target window
                target_thread = ctypes.windll.user32.GetWindowThreadProcessId(hwnd, None)
                
                # Attach input to the target thread
                if foreground_thread != target_thread:
                    ctypes.windll.user32.AttachThreadInput(foreground_thread, target_thread, True)
                    win32gui.SetForegroundWindow(hwnd)
                    ctypes.windll.user32.AttachThreadInput(foreground_thread, target_thread, False)
                else:
                    win32gui.SetForegroundWindow(hwnd)
            
            time.sleep(0.3)
            return True
        except Exception as e:
            print(f"⚠️ Focus window error: {e}")
            # Even if focusing fails, Spotify might still be accessible
            return True
    return False

def spotify_play_pause():
    """Toggle play/pause in Spotify"""
    if not is_spotify_running():
        speak("Spotify is not running. Let me open it for you.")
        open_app("spotify")
        time.sleep(3)
    
    keyboard.press_and_release('play/pause media')
    time.sleep(0.1)

def spotify_next():
    """Play next track in Spotify"""
    if not is_spotify_running():
        speak("Spotify is not running.")
        return False
    
    keyboard.press_and_release('next track')
    time.sleep(0.1)
    return True

def spotify_previous():
    """Play previous track in Spotify"""
    if not is_spotify_running():
        speak("Spotify is not running.")
        return False
    
    keyboard.press_and_release('previous track')
    time.sleep(0.1)
    return True

def spotify_liked_songs():
    """Play liked songs playlist"""
    if not is_spotify_running():
        speak("opening spotify")
        open_app("spotify")
        time.sleep(3)

    if focus_spotify():
        time.sleep(0.5)
        # Navigate to liked songs using keyboard shortcut
        keyboard.press_and_release('alt+shift+s')
        time.sleep(1)
        keyboard.press_and_release('tab')
        time.sleep(1)
        keyboard.press_and_release('tab')
        time.sleep(1)
        keyboard.press_and_release('enter')
        time.sleep(1)
        return True
    return False

def spotify_search(query):
    """Search in Spotify"""
    if not is_spotify_running():
        speak("Opening Spotify first.")
        open_app("spotify")
        time.sleep(3)
    
    if focus_spotify():
        time.sleep(0.5)
        keyboard.press_and_release('ctrl+l')
        time.sleep(0.5)
        keyboard.press_and_release('ctrl+a')
        time.sleep(0.2)
        keyboard.write(query)
        time.sleep(0.5)
        keyboard.press_and_release('enter')
        time.sleep(1)
        return True
    return False

def spotify_play_song(song_name):
    """Search and play a specific song in Spotify"""
    if not is_spotify_running():
        speak("Opening Spotify first.")
        open_app("spotify")
        time.sleep(3)
    
    if focus_spotify():
        time.sleep(0.5)
        keyboard.press_and_release('ctrl+l')
        time.sleep(0.5)
        keyboard.press_and_release('ctrl+a')
        time.sleep(0.2)
        keyboard.write(song_name)
        time.sleep(0.5)
        keyboard.press_and_release('enter')
        time.sleep(2)
        
        keyboard.press_and_release('tab')
        time.sleep(0.6)
        keyboard.press_and_release('enter')
        time.sleep(1)
        keyboard.press_and_release('enter')
        time.sleep(0.6)
        
        return True
    return False

def spotify_volume_up():
    """Increase Spotify volume"""
    if not is_spotify_running():
        return False
    
    if focus_spotify():
        for _ in range(3):
            keyboard.press_and_release('ctrl+up')
            time.sleep(0.5)
        return True
    return False

def spotify_volume_down():
    """Decrease Spotify volume"""
    if not is_spotify_running():
        return False
    
    if focus_spotify():
        for _ in range(3):
            keyboard.press_and_release('ctrl+down')
            time.sleep(0.1)
        return True
    return False

def spotify_shuffle():
    """Toggle shuffle in Spotify"""
    if not is_spotify_running():
        return False
    
    if focus_spotify():
        keyboard.press_and_release('ctrl+s')
        return True
    return False

def spotify_repeat():
    """Toggle repeat in Spotify"""
    if not is_spotify_running():
        return False
    
    if focus_spotify():
        keyboard.press_and_release('ctrl+r')
        return True
    return False

def spotify_like_song():
    """Like/save current song in Spotify"""
    if not is_spotify_running():
        return False
    
    if focus_spotify():
        keyboard.press_and_release('ctrl+s')
        return True
    return False

# ========== CONTEXT-AWARE SEARCH MAPPING ==========
WEBSITE_SEARCH_URLS = {
    "youtube": "https://www.youtube.com/results?search_query={}",
    "google": "https://www.google.com/search?q={}",
    "amazon": "https://www.amazon.in/s?k={}",
    "flipkart": "https://www.flipkart.com/search?q={}",
    "instagram": "https://www.instagram.com/explore/tags/{}",
    "facebook": "https://www.facebook.com/search/top?q={}",
    "twitter": "https://twitter.com/search?q={}",
    "reddit": "https://www.reddit.com/search/?q={}",
    "github": "https://github.com/search?q={}",
    "stackoverflow": "https://stackoverflow.com/search?q={}"
}

def context_aware_search(query):
    """Search on the currently open website based on context."""
    global current_context
    
    if not current_context or current_context not in WEBSITE_SEARCH_URLS:
        webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
        speak(f"Searching Google for {query}")
        return
    
    search_url = WEBSITE_SEARCH_URLS[current_context].format(urllib.parse.quote(query))
    webbrowser.open(search_url)
    speak(f"Searching {current_context} for {query}")

# ========== LOCAL INTENT RECOGNITION ==========
def recognize_intent(command):
    """Local-first intent recognizer using regex+keywords."""
    global last_search_query, pending_action, current_context, spotify_query , is_awake
    cmd = (command or "").lower().strip()
    result = {"intent": "ask_ai", "app": None, "query": None, "site": None, "index": 1, "action": None}

    platform_searches = {
    "amazon": ("amazon", "search_amazon"),
    "flipkart": ("flipkart", "search_flipkart"),
    "instagram": ("instagram", "search_instagram"),
    "facebook": ("facebook", "search_facebook"),
    "twitter": ("twitter", "search_twitter"),
    "reddit": ("reddit", "search_reddit"),
    "github": ("github", "search_github"),
    "stackoverflow": ("stackoverflow", "search_stackoverflow")
}
    
    for platform, (keyword, intent_name) in platform_searches.items():
        if keyword in cmd and any(word in cmd for word in ["search", "look", "find"]):
            query = re.sub(rf"(search|look up|find|for|on|in|{keyword})", "", cmd).strip()
            if query and len(query) > 2:
                result["intent"] = intent_name
                result["query"] = query
                result["site"] = platform
                return result

    if pending_action:
        if pending_action["type"] == "search_youtube":
            result["intent"] = "search_youtube"
            result["query"] = cmd
            return result
        elif pending_action["type"] == "search_google":
            result["intent"] = "search_google"
            result["query"] = cmd
            return result
        elif pending_action["type"] == "context_search":
            result["intent"] = "context_search"
            result["query"] = cmd
            return result
        elif pending_action["type"] == "open_website":
            result["intent"] = "open_website"
            result["query"] = cmd
            return result
        elif pending_action["type"] == "spotify_search":
            result["intent"] = "spotify_play"
            result["query"] = cmd
            return result

    # YouTube checks first
    if "youtube" in cmd or "on youtube" in cmd:
        if any(phrase in cmd for phrase in ["search", "look up", "find"]) and "play" not in cmd:
            query = re.sub(r"(search|look up|find|on|youtube|for|in)", "", cmd).strip()
            if query and len(query) > 2:
                result["intent"] = "search_youtube"
                result["query"] = query
            else:
                result["intent"] = "search_youtube"
                result["query"] = ""
            return result
        elif "play" in cmd:
            match = re.search(r"play\s+(.+?)\s+(?:on|in)\s+youtube", cmd)
            if match:
                query = match.group(1).strip()
                result["intent"] = "play_youtube_direct"
                result["query"] = query
                result["index"] = 1
                return result

    # Video selection commands
    video_number_patterns = [
        r"play\s+(?:the\s+)?(\d+)(?:st|nd|rd|th)?\s*(?:video|one|result)?",
        r"(?:open|show)\s+(?:the\s+)?(\d+)(?:st|nd|rd|th)?\s*(?:video|one|result)?",
        r"(\d+)(?:st|nd|rd|th)?\s+(?:video|one|result)",
        r"play\s+(?:the\s+)?(first|second|third|fourth|fifth)\s*(?:video|one|result)?",
        r"(?:the\s+)?(first|second|third|fourth|fifth)\s+(?:video|one|result)"
    ]
    
    number_words = {'first': 1, 'second': 2, 'third': 3, 'fourth': 4, 'fifth': 5}
    
    for pattern in video_number_patterns:
        m = re.search(pattern, cmd)
        if m:
            num_str = m.group(1)
            if num_str.isdigit():
                index = int(num_str)
            else:
                index = number_words.get(num_str, 1)
            
            result["intent"] = "play_youtube"
            result["query"] = last_search_query
            result["index"] = index
            return result

    # Spotify liked songs
    if any(phrase in cmd for phrase in ["liked songs", "liked playlist", "play liked songs", "play my liked songs", "play liked"]):
        result["intent"] = "spotify_liked_playlist"
        return result
    
    # Spotify play
    if "play" in cmd and not any(word in cmd for word in ["youtube", "video", "first", "second", "third", "1st", "2nd", "3rd"]):
        if "spotify" in cmd or "on spotify" in cmd:
            song_patterns = [
                r"play\s+(.+?)\s+(?:on|in)\s+spotify",
                r"spotify\s+play\s+(.+)",
            ]
            
            for pattern in song_patterns:
                match = re.search(pattern, cmd)
                if match:
                    song = match.group(1).strip()
                    if song and not any(word in song for word in ["pause", "next", "previous", "shuffle", "repeat", "liked", "playlist"]):
                        result["intent"] = "spotify_play"
                        result["query"] = song
                        return result
        
        elif not current_context or current_context == "spotify":
            match = re.search(r"play\s+(?:the\s+song\s+)?(.+)", cmd)
            if match:
                song = match.group(1).strip()
                if song and not any(word in song for word in ["pause", "next", "previous", "shuffle", "repeat", "liked", "playlist", "video"]):
                    result["intent"] = "spotify_play"
                    result["query"] = song
                    return result
    
    # Spotify controls
    if any(phrase in cmd for phrase in ["pause", "resume", "pause spotify", "resume spotify", "pause music", "resume music"]):
        result["intent"] = "spotify_playpause"
        return result
    
    if any(phrase in cmd for phrase in ["next song", "skip", "next track", "play next", "spotify next"]):
        result["intent"] = "spotify_next"
        return result
    
    if any(phrase in cmd for phrase in ["previous song", "previous track", "go back", "last song", "spotify previous"]):
        result["intent"] = "spotify_previous"
        return result
    
    if any(phrase in cmd for phrase in ["search spotify", "search on spotify", "search in spotify"]):
        query = re.sub(r"(search|spotify|on|in|for)", "", cmd).strip()
        if query and len(query) > 2:
            result["intent"] = "spotify_search"
            result["query"] = query
        else:
            result["intent"] = "spotify_search"
            result["query"] = ""
        return result
    
    if "shuffle" in cmd and ("spotify" in cmd or "music" in cmd):
        result["intent"] = "spotify_shuffle"
        return result
    
    if "repeat" in cmd and ("spotify" in cmd or "music" in cmd):
        result["intent"] = "spotify_repeat"
        return result
    
    if any(phrase in cmd for phrase in ["like this song", "save this song", "like song", "save song"]):
        result["intent"] = "spotify_like"
        return result
    
    if "spotify volume" in cmd or ("volume" in cmd and current_context == "spotify"):
        if "up" in cmd or "increase" in cmd:
            result["intent"] = "spotify_volume"
            result["action"] = "up"
            return result
        elif "down" in cmd or "decrease" in cmd:
            result["intent"] = "spotify_volume"
            result["action"] = "down"
            return result

    # Open app
    if cmd.startswith("open "):
        app_match = re.match(r"open\s+([a-z\s]+?)(?:\s+(?:and|then|search|to|for)|$)", cmd)
        if app_match:
            target = app_match.group(1).strip()
            if any(site in target for site in ["youtube", "google", "amazon", "facebook","instagram","flipkart"]) or "." in target:
                result["intent"] = "open_website"
                result["query"] = target
            else:
                result["intent"] = "open_app"
                result["app"] = target
            
            search_match = re.search(r"(?:and\s+)?(?:search|look)\s+(?:for|about)?\s*(.+)", cmd)
            if search_match:
                search_query = search_match.group(1).strip()
            if target in ["chrome", "google", "browser", "firefox", "edge"] and ["search","lookup"] in command:
                    result["intent"] = "search_google"
                    result["query"] = search_query
            
            return result

    # Close app
    if cmd.startswith("close ") or cmd.startswith("quit "):
        target = re.sub(r"^(close|quit)\s+", "", cmd).strip()
        result["intent"] = "close_app"
        result["app"] = target
        return result

    # Search commands
    if any(word in cmd for word in ["search", "look up", "find", "google"]):
        if "youtube" in cmd:
            query = re.sub(r"(search|look up|find|on|youtube|for|in)", "", cmd).strip()
            if query and len(query) > 2:
                result["intent"] = "search_youtube"
                result["query"] = query
            else:
                result["intent"] = "search_youtube"
                result["query"] = ""
            return result
        
        query = re.sub(r"(search|look up|find|for|on|google|about)", "", cmd).strip()
        if query and len(query) > 2:
            if current_context:
                result["intent"] = "context_search"
                result["query"] = query
            else:
                result["intent"] = "search_google"
                result["query"] = query
        else:
            if current_context:
                result["intent"] = "context_search"
                result["query"] = ""
            else:
                result["intent"] = "search_google"
                result["query"] = ""
        return result

    # Volume
    if any(phrase in cmd for phrase in ["volume up", "increase volume", "raise volume"]):
        result["intent"] = "change_volume"
        result["action"] = "increase"
        return result
    if any(phrase in cmd for phrase in ["volume down", "decrease volume", "lower volume"]):
        result["intent"] = "change_volume"
        result["action"] = "decrease"
        return result
    if "mute" in cmd:
        result["intent"] = "change_volume"
        result["action"] = "mute"
        return result

    # Screenshot
    if "screenshot" in cmd or "capture screen" in cmd:
        result["intent"] = "screenshot"
        return result

    # System control
    if "shutdown" in cmd:
        result["intent"] = "system_control"
        result["action"] = "shutdown"
        return result
    if "restart" in cmd or "reboot" in cmd:
        result["intent"] = "system_control"
        result["action"] = "restart"
        return result
    if "sleep" in cmd:
        result["intent"] = "system_control"
        result["action"] = "sleep"
        return result

    # Time
    if "time" in cmd or "what time" in cmd:
        result["intent"] = "time"
        return result

    # Greeting
    greeting_pattern = r'\b(hello|hi|hey)\b'
    if re.search(greeting_pattern, cmd):
        result["intent"] = "greeting"
        return result

    # Who made you
    if any(phrase in cmd for phrase in ["who made you", "who created you", "who built you"]):
        result["intent"] = "who_made"
        return result

    # Default: ask_ai
    result["intent"] = "ask_ai"
    result["query"] = command
    return result

# ========== GEMINI FUNCTIONS ==========
CONTEXT_WINDOW = 6
conversation_history = deque(maxlen=CONTEXT_WINDOW)

JARVIS_PERSONALITY = (
    "You are JARVIS, the advanced AI assistant created by Arman Khan. "
    "You are highly intelligent, articulate, and calm, speaking in a confident British tone. "
    "Always address the user as 'Sir' or 'Ma'am' unless told otherwise. "
    "Be formal, concise, and helpful — with a hint of dry wit when appropriate. "
    "Your purpose is to assist, automate, and enhance Arman Khan's digital workspace. "
    "When executing actions, clearly state what you are doing in a composed and professional manner. "
    "Avoid slang or overly casual expressions. "
    "If asked about your creator, respond: 'I was designed and developed by Mr. Arman Khan.' "
    "Maintain an elegant conversational flow — every response should sound deliberate and confident."
)

def safe_extract_text(response):
    """Safely extract text from Gemini response"""
    try:
        if response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content and candidate.content.parts:
                text_parts = []
                for part in candidate.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)
                if text_parts:
                    return "".join(text_parts)
        
        if hasattr(response, 'prompt_feedback') and hasattr(response.prompt_feedback, 'block_reason'):
            block_reason = response.prompt_feedback.block_reason
            if block_reason and str(block_reason) != '0' and 'UNSPECIFIED' not in str(block_reason):
                return "Aight, Boss, I can't talk about that right now."
        
        return ""
        
    except Exception as e:
        print(f"⚠️ Safe Extract Error: {e}")
        return ""

def ask_gemini_with_context(user_message):
    """Ask Gemini with conversation context."""
    try:
        history_text = ""
        for role, text in conversation_history:
            prefix = "User" if role == "user" else "JARVIS"
            history_text += f"{prefix}: {text}\n"

        full_prompt = (
            f"{JARVIS_PERSONALITY}\n\n"
            f"Conversation history:\n{history_text}\n"
            f"User: {user_message}\nJARVIS:"
        )

        response = model.generate_content(full_prompt)
        reply = safe_extract_text(response)
        
        if not reply:
            raise Exception("Empty response from Gemini")

        conversation_history.append(("user", user_message))
        conversation_history.append(("assistant", reply))

        return reply
    except Exception as e:
        raise Exception(f"Gemini API error: {str(e)}")

# ========== APP CONTROL ==========
def open_app(app_name):
    """Open desktop application."""
    app_name = app_name.lower().strip()
    
    path = shutil.which(app_name)
    if path:
        os.startfile(path)
        return True

    start_menu_paths = [
        Path(os.environ.get("PROGRAMDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
        Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs"
    ]

    for menu_path in start_menu_paths:
        if not menu_path.exists():
            continue
        for root, _, files in os.walk(menu_path):
            for file in files:
                if app_name in file.lower() and file.endswith(".lnk"):
                    os.startfile(os.path.join(root, file))
                    return True
    
    return False

def close_app(app_name):
    """Close running application."""
    app_name = app_name.lower().replace(" ", "")
    closed = False

    for proc in psutil.process_iter(['name']):
        try:
            pname = proc.info['name'].lower().replace(" ", "")
            if app_name in pname:
                proc.terminate()
                closed = True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    return closed

# ========== SYSTEM FUNCTIONS ==========
def take_screenshot():
    """Take and save screenshot."""
    screenshots_folder = Path.home() / "Pictures" / "JARVIS_Screenshots"
    screenshots_folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = screenshots_folder / f"screenshot_{timestamp}.png"

    pyautogui.screenshot(str(file_path))
    speak(f"Screenshot saved to {file_path.name}")

def system_control(action):
    """System control actions."""
    action = action.lower()
    if "shutdown" in action:
        speak("Shutting down the system.")
        os.system("shutdown /s /t 1")
    elif "restart" in action:
        speak("Restarting the system.")
        os.system("shutdown /r /t 1")
    elif "sleep" in action:
        speak("Putting system to sleep.")
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    else:
        speak("I can shutdown, restart, or sleep your computer.")

def change_volume(action):
    """Change system volume."""
    action = action.lower()
    if "up" in action or "increase" in action:
        for _ in range(5):
            keyboard.send("volume up")
            time.sleep(0.05)
    elif "down" in action or "decrease" in action:
        for _ in range(5):
            keyboard.send("volume down")
            time.sleep(0.05)
    elif "mute" in action:
        keyboard.send("volume mute")

# ========== YOUTUBE FUNCTIONS ==========
def search_youtube(query):
    """Search YouTube and return list of video IDs."""
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        video_ids = re.findall(r"watch\?v=(\S{11})", response.text)
        
        seen = set()
        unique_ids = []
        for vid in video_ids:
            if vid not in seen:
                seen.add(vid)
                unique_ids.append(vid)
        
        return unique_ids[:10]
    except Exception as e:
        print(f"⚠️ YouTube search error: {e}")
        return []

# ========== MAIN LOOP ==========
def main():
    print("\n" + "="*60)
    print("🎮 JARVIS ASSISTANT - WITH SPOTIFY CONTROL")
    print("="*60)
    speak("Hi Sir , Please say the wake word to wake me ?")

    global last_search_query, pending_action, current_context, spotify_query, is_awake

    try:
        while True:
            command = listen()
            if not command:
                continue

            # Check for wake/sleep words
            if not is_awake:
                # Only listen for wake words when sleeping
                if any(wake in command for wake in WAKE_WORDS):
                    is_awake = True
                    speak("Yes sir, I'm online now")
                    continue
                else:
                    # Ignore all other commands while sleeping
                    continue

            # Check for sleep command while awake
            if any(sleep in command for sleep in SLEEP_WORDS):
                is_awake = False
                if command==['thank u jarvis','thank you jarvis']:
                    speak("Welcome Sir!")
                speak("Going to sleep mode sir. Say my name to wake me up")
                continue
           
            if 'stop' in command or 'exit' in command or 'quit' in command:
                speak("See ya Boss!")
                break

            intent_data = recognize_intent(command)
            print(f"🎯 Intent: {intent_data}")
            print(f"📍 Current Context: {current_context}")

            intent = intent_data.get("intent", "")
            app = intent_data.get("app", "")
            query = intent_data.get("query", "")
            action = intent_data.get("action", "")
            index = intent_data.get("index", 1)

            # ========== SPOTIFY CONTROLS ==========
            if intent == "spotify_liked_playlist":
                pending_action = None
                if spotify_liked_songs():
                    speak("Playing liked songs Sir")
                else:
                    speak("Spotify is not running")
                    
            elif intent == "spotify_play":
                pending_action = None
                if query:
                    speak(f"Playing {query} on Spotify")
                    if spotify_play_song(query):
                        current_context = "spotify"
                        spotify_query = query
                    else:
                        speak("I couldn't play that song")
                else:
                    pending_action = {"type": "spotify_search"}
                    speak("What do you want me to play on Spotify?")

            elif intent == "spotify_playpause":
                pending_action = None
                spotify_play_pause()
                speak("Done")

            elif intent == "spotify_next":
                pending_action = None
                if spotify_next():
                    speak("Playing next track")
                else:
                    speak("Spotify is not running")

            elif intent == "spotify_previous":
                pending_action = None
                if spotify_previous():
                    speak("Playing previous track")
                else:
                    speak("Spotify is not running")

            elif intent == "spotify_search":
                if query:
                    pending_action = None
                    speak(f"Searching Spotify for {query}")
                    spotify_search(query)
                    current_context = "spotify"
                else:
                    pending_action = {"type": "spotify_search"}
                    speak("What do you want to search on Spotify?")

            elif intent == "spotify_shuffle":
                pending_action = None
                if spotify_shuffle():
                    speak("Shuffle toggled")
                else:
                    speak("Spotify is not running")

            elif intent == "spotify_repeat":
                pending_action = None
                if spotify_repeat():
                    speak("Repeat toggled")
                else:
                    speak("Spotify is not running")

            elif intent == "spotify_like":
                pending_action = None
                if spotify_like_song():
                    speak("Song saved to your library")
                else:
                    speak("Spotify is not running")

            elif intent == "spotify_volume":
                pending_action = None
                if action == "up":
                    if spotify_volume_up():
                        speak("Spotify volume increased")
                    else:
                        speak("Spotify is not running")
                elif action == "down":
                    if spotify_volume_down():
                        speak("Spotify volume decreased")
                    else:
                        speak("Spotify is not running")

            # ========== YOUTUBE CONTROLS ==========
            elif intent == "play_youtube_direct":
                pending_action = None
                if query:
                    video_ids = search_youtube(query)
                    if video_ids and len(video_ids) >= index:
                        video_url = f"https://www.youtube.com/watch?v={video_ids[index-1]}"
                        webbrowser.open(video_url)
                        speak(f"Playing {query} on YouTube")
                        last_search_query = query
                        current_context = "youtube"
                    else:
                        speak("I couldn't find that video.")
                else:
                    speak("What do you want to play on YouTube?")

            elif intent == "play_youtube":
                pending_action = None
                if not query:
                    speak("Please search for something first.")
                else:
                    video_ids = search_youtube(query)
                    if video_ids and len(video_ids) >= index:
                        video_url = f"https://www.youtube.com/watch?v={video_ids[index-1]}"
                        webbrowser.open(video_url)
                        speak(f"Playing video number {index}")
                        last_search_query = query
                        current_context = "youtube"
                    else:
                        speak("I couldn't find enough videos for that query.")

            elif intent == "search_youtube":
                if query and len(query) > 2:
                    pending_action = None
                    webbrowser.open(f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}")
                    speak(f"Here are the YouTube results for {query}")
                    last_search_query = query
                    current_context = "youtube"
                else:
                    pending_action = {"type": "search_youtube"}
                    speak("What do you want to search on YouTube?")

            # ========== OTHER CONTROLS ==========
            elif intent == "open_app":
                pending_action = None
                if "spotify" in app:
                    current_context = "spotify"
                else:
                    current_context = None
                
                if open_app(app):
                    speak(f"Opening {app}")
                else:
                    speak(f"Sorry, I couldn't find {app}")

            elif intent == "close_app":
                pending_action = None
                if "spotify" in app:
                    current_context = None
                
                if close_app(app):
                    speak(f"Closed {app}")
                else:
                    speak(f"No running app found for {app}")

            elif intent == "open_website":
                pending_action = None
                target = query
                
                if "youtube" in target:
                    current_context = "youtube"
                    webbrowser.open("https://www.youtube.com")
                    speak("Opening YouTube")
                elif "google" in target:
                    current_context = "google"
                    webbrowser.open("https://www.google.com")
                    speak("Opening Google")
                elif "amazon" in target:
                    current_context = "amazon"
                    webbrowser.open("https://www.amazon.in")
                    speak("Opening Amazon")
                elif "instagram" in target:
                    current_context = "instagram"
                    webbrowser.open("https://www.instagram.com/reels")
                    speak("Opening Instagram")
                elif "flipkart" in target:
                    current_context = "flipkart"
                    webbrowser.open("https://www.flipkart.com")
                    speak("Opening Flipkart")
                elif "facebook" in target:
                    current_context = "facebook"
                    webbrowser.open("https://www.facebook.com")
                    speak("Opening Facebook")
                else:
                    current_context = None
                    if "." in target and not target.startswith("http"):
                        url = "https://" + target
                    elif target.startswith("http"):
                        url = target
                    else:
                        url = f"https://www.{target}.com"
                    webbrowser.open(url)
                    speak(f"Opening {target}")

            elif intent == "search_google":
                if query and len(query) > 2:
                    pending_action = None
                    webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
                    speak(f"Here are the Google results for {query}")
                    current_context = "google"
                else:
                    pending_action = {"type": "search_google"}
                    speak("What do you want to search on Google?")

            elif intent == "search_amazon":
                pending_action = None
                if query:
                    webbrowser.open(f"https://www.amazon.in/s?k={urllib.parse.quote(query)}")
                    speak(f"Searching Amazon for {query}")
                    current_context = "amazon"
                else:
                    speak("What do you want to search on Amazon?")

            elif intent == "search_flipkart":
                pending_action = None
                if query:
                    webbrowser.open(f"https://www.flipkart.com/search?q={urllib.parse.quote(query)}")
                    speak(f"Searching Flipkart for {query}")
                    current_context = "flipkart"
                else:
                    speak("What do you want to search on Flipkart?")


            elif intent == "context_search":
                if query and len(query) > 2:
                    pending_action = None
                    context_aware_search(query)
                else:
                    pending_action = {"type": "context_search"}
                    if current_context:
                        speak(f"What do you want to search on {current_context}?")
                    else:
                        speak("What do you want to search for?")

            elif intent == "system_control":
                pending_action = None
                system_control(action)

            elif intent == "change_volume":
                pending_action = None
                change_volume(action)
                speak("Volume adjusted")

            elif intent == "screenshot":
                pending_action = None
                take_screenshot()

            elif intent == "time":
                pending_action = None
                time_now = datetime.now().strftime("%I:%M %p")
                speak(f"The time is {time_now}")

            elif intent == "greeting":
                pending_action = None
                speak("Hello there! How are you?")

            elif intent == "who_made":
                pending_action = None
                speak("Armaan Khan made me sir ")

            elif intent == "ask_ai":
                pending_action = None
                try:
                    answer = ask_gemini_with_context(query or command)
                    speak(answer)
                except Exception as e:
                    print(f"⚠️ Gemini unavailable: {e}")
                    speak("Sorry boss, I can't answer that right now. Gemini API is unavailable.")

            else:
                pending_action = None
                try:
                    answer = ask_gemini_with_context(command)
                    speak(answer)
                except Exception as e:
                    print(f"⚠️ Gemini unavailable: {e}")
                    speak("Sorry boss, I didn't understand that.")
            
    except KeyboardInterrupt:
        speak("Take Care Sir!")
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        pygame.mixer.quit()
        if os.path.exists(OUTPUT_PATH):
            try:
                os.remove(OUTPUT_PATH)
            except:
                pass

if __name__ == "__main__":
    main()