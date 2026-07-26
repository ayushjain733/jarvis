import os
import urllib.request
import urllib.parse
import re
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from duckduckgo_search import DDGS

# Check if running locally based on our .env file
IS_LOCAL = os.environ.get("ENVIRONMENT") == "local"

# ---------------------------------------------------------
# UNIVERSAL TOOLS (Work everywhere)
# ---------------------------------------------------------
@tool
def read_local_file(file_path: str) -> str:
    """Reads the contents of a text or PDF file."""
    if not os.path.exists(file_path):
        return f"File not found at: {file_path}"
    try:
        if file_path.lower().endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read(3000)
        elif file_path.lower().endswith('.pdf'):
            import pypdf
            text = ""
            with open(file_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                for page in reader.pages[:5]:
                    text += page.extract_text() or ""
            return text[:3000] if text else "PDF is empty."
        return "Unsupported file extension."
    except Exception as e:
        return f"Error reading file: {e}"

@tool
def play_music_on_youtube(song_name: str) -> str:
    """Searches YouTube for a song."""
    try:
        query = urllib.parse.quote(song_name)
        url = f"https://www.youtube.com/results?search_query={query}"
        html = urllib.request.urlopen(url)
        video_ids = re.findall(r"watch\?v=(\S{11})", html.read().decode())
        if video_ids:
            video_url = f"https://www.youtube.com/watch?v={video_ids[0]}"
            if IS_LOCAL:
                import webbrowser
                webbrowser.open(video_url)
                return f"Successfully opened and playing {song_name} on YouTube."
            else:
                return f"I found the song! [Click here to play {song_name} on YouTube]({video_url})"
        return "Song not found on YouTube."
    except Exception as e:
        return f"Error playing music: {e}"
    
@tool
def web_search(query: str) -> str:
    """
    Searches the internet for real-time information, latest news, or product comparisons.
    Use this when you need up-to-date facts that fall outside your training data.
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
            if not results:
                return "No results found on the web."
            
            formatted_results = "\n\n".join(
                [f"Title: {res['title']}\nSnippet: {res['body']}\nLink: {res['href']}" for res in results]
            )
            return formatted_results
    except Exception as e:
        return f"Web search failed: {e}"

# Start the tool list with universal tools
jarvis_tools = [read_local_file, play_music_on_youtube, web_search]

# ---------------------------------------------------------
# LOCAL-ONLY TOOLS (Skipped in Cloud)
# ---------------------------------------------------------
if IS_LOCAL:
    import subprocess
    import pyautogui
    import base64
    from io import BytesIO

    @tool
    def open_system_path_or_folder(target: str) -> str:
        """Opens any folder, directory, or file on the Windows system."""
        try:
            if os.path.exists(target):
                os.startfile(target)
                return f"Successfully opened path: {target}"
            
            user_profile = os.environ.get("USERPROFILE", "C:\\Users\\Default")
            common_dirs = [
                os.path.join(user_profile, "Downloads"),
                os.path.join(user_profile, "Desktop"),
                os.path.join(user_profile, "Documents"),
                "C:\\"
            ]
            target_clean = target.lower().strip()
            for cdir in common_dirs:
                if os.path.basename(cdir).lower() == target_clean:
                    os.startfile(cdir)
                    return f"Opened {cdir} directory."

            for base_dir in common_dirs:
                if not os.path.exists(base_dir):
                    continue
                for item in os.listdir(base_dir):
                    if target_clean in item.lower():
                        full_path = os.path.join(base_dir, item)
                        os.startfile(full_path)
                        return f"Found and opened: {full_path}"
            return f"Could not locate '{target}'."
        except Exception as e:
            return f"Failed to open path: {e}"

    @tool
    def launch_app_or_setting(app_or_setting: str) -> str:
        """Launches system apps or Windows settings."""
        target = app_or_setting.lower().strip()
        settings_map = {
            "settings": "ms-settings:", "bluetooth": "ms-settings:bluetooth",
            "display": "ms-settings:display", "network": "ms-settings:network"
        }
        app_map = {
            "notepad": "notepad.exe", "calculator": "calc.exe",
            "cmd": "cmd.exe", "vscode": "code", "chrome": "chrome"
        }
        try:
            if target in settings_map:
                os.system(f"start {settings_map[target]}")
                return f"Opened {target} settings."
            elif target in app_map:
                subprocess.Popen(app_map[target], shell=True)
                return f"Opened application: {target}"
            else:
                subprocess.Popen(target, shell=True)
                return f"Attempted to launch: {target}"
        except Exception as e:
            return f"Failed to launch '{app_or_setting}': {e}"

    @tool
    def change_volume(action: str, amount: int = 5) -> str:
        """Changes system volume (up, down, mute)."""
        try:
            if action == "mute":
                pyautogui.press("volumemute")
                return "Volume muted."
            key = "volumeup" if action == "up" else "volumedown"
            for _ in range(amount):
                pyautogui.press(key)
            return f"Adjusted volume {action}."
        except Exception as e:
            return f"Failed to adjust volume: {e}"

    @tool
    def analyze_screen(prompt: str = "Describe what you see on this screen in detail.") -> str:
        """Takes a screenshot of the user's screen and analyzes it."""
        try:
            screenshot = pyautogui.screenshot()
            buffered = BytesIO()
            screenshot.save(buffered, format="JPEG")
            img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
            vision_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
            msg = HumanMessage(content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
            ])
            return vision_llm.invoke([msg]).content
        except Exception as e:
            return f"Failed to analyze screen: {e}"

    # Append the local tools only if we are running locally
    jarvis_tools.extend([open_system_path_or_folder, launch_app_or_setting, change_volume, analyze_screen])