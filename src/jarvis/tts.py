import asyncio
import edge_tts
import tempfile
import os

class TextToSpeech:
    def __init__(self, voice="en-US-ChristopherNeural"):
        self.voice = voice

    def generate_audio(self, text: str) -> bytes:
        """Generates TTS and returns it as audio bytes for the browser."""
        return asyncio.run(self._async_generate(text))

    async def _async_generate(self, text: str) -> bytes:
        communicate = edge_tts.Communicate(text, self.voice)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_path = tmp_file.name
        
        await communicate.save(tmp_path)
        
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()
            
        os.remove(tmp_path)
        return audio_bytes