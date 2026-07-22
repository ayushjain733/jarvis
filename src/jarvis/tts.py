import asyncio
import edge_tts
import pygame
import tempfile
import os

class TextToSpeech:
    def __init__(self, voice="en-US-ChristopherNeural"): # Professional, deep male voice
        self.voice = voice
        pygame.mixer.init()

    def speak(self, text: str):
        # Bridge the async TTS generation into our synchronous Jarvis loop
        asyncio.run(self._async_speak(text))

    async def _async_speak(self, text: str):
        communicate = edge_tts.Communicate(text, self.voice)
        
        # Save audio to a temporary mp3 file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
            tmp_path = tmp_file.name
        
        await communicate.save(tmp_path)
        
        # Play the audio using pygame
        pygame.mixer.music.load(tmp_path)
        pygame.mixer.music.play()
        
        # Wait for the audio to finish playing before allowing Jarvis to listen again
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
        pygame.mixer.music.unload()
        os.remove(tmp_path)