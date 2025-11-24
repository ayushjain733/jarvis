import speech_recognition as sr
import webbrowser
import pyttsx3
import sys
import musicLibrary
import os


r = sr.Recognizer()

_tts_backend = None
_tts_obj = None


def init_tts():
    """Initialize a TTS backend and return a tuple (backend_name, backend_obj).

    backend_name is one of: 'win32com', 'pyttsx3-sapi5', 'pyttsx3', 'print'
    backend_obj is either the COM speaker or pyttsx3 engine (or None).
    """
    global _tts_backend, _tts_obj
    if _tts_backend is not None:
        return _tts_backend, _tts_obj

    # Try win32com SAPI first (very reliable on Windows)
    try:
        import win32com.client
        speaker = win32com.client.Dispatch("SAPI.SpVoice")
        _tts_backend = 'win32com'
        _tts_obj = speaker
        return _tts_backend, _tts_obj
    except Exception as e:
        print(f"win32com init failed: {e}")

    # Try pyttsx3 with sapi5
    try:
        engine = pyttsx3.init('sapi5')
        _tts_backend = 'pyttsx3-sapi5'
        _tts_obj = engine
        return _tts_backend, _tts_obj
    except Exception as e:
        print(f"pyttsx3 sapi5 init failed: {e}")

    # Try generic pyttsx3
    try:
        engine = pyttsx3.init()
        _tts_backend = 'pyttsx3'
        _tts_obj = engine
        return _tts_backend, _tts_obj
    except Exception as e:
        print(f"pyttsx3 init failed: {e}")

    # Final fallback: no TTS available
    _tts_backend = 'print'
    _tts_obj = None
    return _tts_backend, _tts_obj


def speak(text):
    if not text:
        return
    backend, obj = init_tts()

    try:
        if backend == 'win32com' and obj is not None:
            try:
                obj.Speak(str(text))
            except KeyboardInterrupt:
                # allow user to interrupt speaking (e.g., Ctrl-C)
                try:
                    # stop speaking if COM object supports it
                    obj.Skip("SENTENCE")
                except Exception:
                    pass
                return
            return

        if backend in ('pyttsx3-sapi5', 'pyttsx3') and obj is not None:
            obj.say(str(text))
            obj.runAndWait()
            return
    except Exception as e:
        print(f"TTS backend '{backend}' error: {e}")

    # Last resort: print the text so user still sees it
    print("TTS fallback:", text)

def processCommand(c):
    print(c)
    # allow an explicit sleep/shutdown command to terminate the program
    cl = c.lower().strip()
    if cl in ("sleep", "shutdown", "exit", "quit", "stop", "jarvis sleep"):
        speak("Going to sleep. Goodbye.")
        sys.exit(0)
    if "open google" in c.lower():
        webbrowser.open("https://google.com")
    elif "open youtube" in c.lower():
        webbrowser.open("https://youtube.com")
    elif "open gmail" in c.lower():
        webbrowser.open("https://gmail.com")
    elif "open facebook" in c.lower():
        webbrowser.open("https://facebook.com")
    elif "open instagram" in c.lower():
        webbrowser.open("https://instagram.com")
    elif "open linkedin" in c.lower():
        webbrowser.open("https://linkedin.com")
    elif "open leetcode" in c.lower():
        webbrowser.open("https://leetcode.com")
    elif "open x" in c.lower():
        webbrowser.open("https://x.com")
    elif "open spotify" in c.lower():
        webbrowser.open("https://open.spotify.com")
    elif "open chatgpt" in c.lower():
        webbrowser.open("https://chatgpt.com")
    elif c.lower().startswith("play"):
        song=c.lower().split(" ")[1]
        link=musicLibrary.music[song]
        webbrowser.open(link)

    else:
        # handle with a small local, open-source LLM (Hugging Face)
        try:
            # lazy import and model init so usual commands stay fast
            def get_llm_pipeline():
                # keep model/tokenizer cached on the function object
                if hasattr(get_llm_pipeline, "cached") and get_llm_pipeline.cached is not None:
                    return get_llm_pipeline.cached

                # Import here to avoid heavy imports when not needed
                from transformers import AutoModelForCausalLM, AutoTokenizer
                import torch

                # Allow selecting a model via environment variable; default to a
                # 1.1B–1.3B-class model per your request (may be slow on CPU).
                requested = os.getenv("JARVIS_MODEL", "bigscience/bloom-1b1")

                # Try the requested model first, with a safe fallback order
                fallback_models = [requested, "EleutherAI/gpt-neo-1.3B", "EleutherAI/gpt-neo-125M"]
                last_exc = None
                for model_name in fallback_models:
                    try:
                        tokenizer = AutoTokenizer.from_pretrained(model_name)
                        model = AutoModelForCausalLM.from_pretrained(model_name)
                        break
                    except Exception as e:
                        print(f"Failed to load {model_name}: {e}")
                        last_exc = e
                else:
                    # All attempts failed
                    raise RuntimeError(f"Could not load any model ({fallback_models})") from last_exc

                # Ensure tokenizer has a pad token
                if tokenizer.pad_token is None:
                    tokenizer.pad_token = tokenizer.eos_token

                # Put model on CPU explicitly
                model.to("cpu")
                model.eval()

                get_llm_pipeline.cached = (tokenizer, model)
                return get_llm_pipeline.cached

            def generate_response(prompt_text):
                tokenizer, model = get_llm_pipeline()
                import torch
                from time import time

                # Build a clearer prompt to encourage direct answers
                prompt = f"Q: {prompt_text.strip()}\nA:"

                input_ids = tokenizer.encode(prompt, return_tensors="pt")
                input_ids = input_ids.to("cpu")

                max_new_tokens = 200
                max_length = input_ids.shape[1] + max_new_tokens

                # Generation parameters tuned to reduce repetition and improve coherence
                gen_kwargs = dict(
                    max_length=max_length,
                    do_sample=True,
                    temperature=0.7,
                    top_p=0.9,
                    top_k=40,
                    repetition_penalty=1.15,
                    no_repeat_ngram_size=3,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                )

                t0 = time()
                with torch.no_grad():
                    outputs = model.generate(input_ids, **gen_kwargs)
                t1 = time()

                text = tokenizer.decode(outputs[0], skip_special_tokens=True)

                # Remove the prompt part and return the completion only
                if text.startswith(prompt):
                    completion = text[len(prompt):].strip()
                else:
                    # If prompt not found, try to drop the input prefix by token length
                    completion = text

                print(f"Generation took {t1-t0:.2f}s")
                return completion

            response = generate_response(c)
            print("LLM response:", response)
            if response:
                speak(response)
            else:
                speak("Sorry, I couldn't generate a response.")
        except Exception as e:
            print(f"LLM error: {e}")
            speak("Sorry, I couldn't process that request.")


if __name__=='__main__':
    # initialize TTS backend once and report it
    backend, _ = init_tts()
    print(f"Using TTS backend: {backend}")
    speak("Initializing jarvis.....")
    while (True):
        try:
            # listen for jarvis
            with sr.Microphone() as source:
                print('Listening...')
                audio=r.listen(source, timeout=2, phrase_time_limit=1)
            # recognize speech using google
            word=r.recognize_google(audio)
            if(word.lower()=="jarvis"):
                speak("Ya")
                # listen for command
                with sr.Microphone() as source:
                    print('Jarvis active...')
                    a=r.listen(source) # a in short for audio

                # recognize speech after releasing the microphone so
                # the TTS engine can access audio output without conflict
                try:
                    command=r.recognize_google(a)
                    processCommand(command)
                except Exception as e:
                    print(f"Error recognizing command: {e}")
                    speak("Sorry, I didn't catch that.")

            
        except Exception as e:
            print (f"Error : {e}")


