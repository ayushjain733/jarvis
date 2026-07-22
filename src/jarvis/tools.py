import os
import subprocess
import urllib.request
import urllib.parse
import re
import webbrowser
import pyautogui
import base64
from io import BytesIO
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

@tool
def play_music_on_youtube(song_name: str) -> str:
    """Searches YouTube for a song and automatically plays the first result."""
    try:
        query = urllib.parse.quote(song_name)
        url = f"https://www.youtube.com/results?search_query={query}"
        html = urllib.request.urlopen(url)
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        if video_ids:
            webbrowser.open(f"https://www.youtube.com/watch?v={video_ids[0]}")
            return f"Playing {song_name} on YouTube."
        return "Could not find the song."
    except Exception as e:
        return f"Error: {e}"

@tool
def open_application(app_name: str) -> str:
    """Opens standard system applications (vscode, settings, notepad, chrome)."""
    app_map = {
        "notepad": "notepad.exe",
        "vscode": "code",
        "settings": "start ms-settings:",
        "chrome": "chrome"
    }
    app_cmd = app_map.get(app_name.lower())
    if app_cmd:
        try:
            subprocess.Popen(app_cmd, shell=True) 
            return f"Opened {app_name}."
        except Exception as e:
            return f"Failed to open {app_name}: {e}"
    return f"Application '{app_name}' is not recognized."

@tool
def read_local_file(file_path: str) -> str:
    """Reads the text contents of a local .txt or .pdf file."""
    if not os.path.exists(file_path):
        return f"File not found at {file_path}"
    
    try:
        if file_path.lower().endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read(2000) # Limit to 2000 characters to prevent overwhelming the LLM
        elif file_path.lower().endswith('.pdf'):
            import pypdf
            text = ""
            with open(file_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                for page in reader.pages[:3]: # Read up to 3 pages
                    text += page.extract_text()
            return text[:2000]
        return "Unsupported file type. Only .txt and .pdf are supported."
    except Exception as e:
        return f"Error reading file: {e}"

@tool
def change_volume(action: str, amount: int = 5) -> str:
    """Changes system volume. Action must be 'up', 'down', or 'mute'. Amount is keystrokes (default 5)."""
    try:
        if action == "mute":
            pyautogui.press("volumemute")
            return "Volume muted."
        
        key = "volumeup" if action == "up" else "volumedown"
        for _ in range(amount):
            pyautogui.press(key)
        return f"Turned volume {action}."
    except Exception as e:
        return f"Failed to change volume: {e}"

@tool
def analyze_screen(prompt: str = "Describe what you see on this screen in detail.") -> str:
    """Takes a screenshot of the user's screen and analyzes it. Use when asked 'what am i seeing'."""
    try:
        screenshot = pyautogui.screenshot()
        buffered = BytesIO()
        screenshot.save(buffered, format="JPEG")
        img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        vision_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
        msg = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
            ]
        )
        return vision_llm.invoke([msg]).content
    except Exception as e:
        return f"Failed to analyze the screen: {e}"

jarvis_tools = [play_music_on_youtube, open_application, read_local_file, change_volume, analyze_screen]