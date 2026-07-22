import os
import speech_recognition as sr
from faster_whisper import WhisperModel
from dotenv import load_dotenv
from agent import jarvis_agent
from tts import TextToSpeech 

load_dotenv()

class JarvisAssistant:
    def __init__(self):
        print("Initializing Jarvis...")
        self.tts = TextToSpeech()
        self.recognizer = sr.Recognizer()
        
        # Load the local Whisper model (Using "base" model for a great balance of speed and accuracy)
        print("Loading local Whisper model...")
        self.whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
        
        # Configure a permanent thread_id so SqliteSaver knows which memory bank to load 
        self.config = {"configurable": {"thread_id": "jarvis-persistent-session"}} #

    def listen(self):
        with sr.Microphone() as source:
            print("\nListening...")
            self.recognizer.adjust_for_ambient_noise(source)
            try:
                # Capture audio
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
                
                # Temporarily save audio for faster-whisper to transcribe
                with open("temp_audio.wav", "wb") as f:
                    f.write(audio.get_wav_data())

                # Transcribe locally
                segments, _ = self.whisper_model.transcribe("temp_audio.wav", beam_size=5)
                command = "".join(segment.text for segment in segments).strip().lower()
                
                os.remove("temp_audio.wav") # Clean up temp file
                
                if command:
                    print(f"You: {command}")
                    return command
                return None

            except sr.WaitTimeoutError:
                return None
            except Exception as e:
                print(f"Error during listening: {e}")
                return None

    def process_command(self, command: str):
        if any(word in command for word in ["stop", "exit", "quit", "shutdown", "sleep"]):
            self.tts.speak("Shutting down core systems. Goodbye.")
            return False

        try:
            # Invoke the LangGraph agent, passing the memory config
            result = jarvis_agent.invoke(
                {"messages": [{"role": "user", "content": command}]},
                config=self.config
            )
            
            final_response = result["messages"][-1].content
            print(f"Jarvis: {final_response}")
            self.tts.speak(final_response)
            
        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {e}"
            print(error_msg)
            self.tts.speak(error_msg)
            
        return True

    def run(self):
        self.tts.speak("All systems online. Jarvis is ready.")
        active = True
        while active:
            command = self.listen()
            if command:
                active = self.process_command(command)

if __name__ == "__main__":
    jarvis = JarvisAssistant()
    jarvis.run()