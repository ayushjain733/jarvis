import streamlit as st
import os
from faster_whisper import WhisperModel
from agent import jarvis_agent
from tts import TextToSpeech

# Ensure a directory exists for uploaded files
os.makedirs("downloads", exist_ok=True)

# Set page configuration for a modern look
st.set_page_config(page_title="Jarvis AI", page_icon="🤖", layout="wide")
st.title("🤖 Jarvis System Terminal")

# Initialize persistent models in session state to avoid reloading
if "whisper" not in st.session_state:
    st.session_state.whisper = WhisperModel("base", device="cpu", compute_type="int8")
if "tts" not in st.session_state:
    st.session_state.tts = TextToSpeech()
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Sidebar for session/thread management
with st.sidebar:
    st.header("Chat Sessions")
    # You can expand this to load thread_ids dynamically from SQLite
    thread_id = st.text_input("Session ID", value="jarvis-persistent-session")
    st.caption("Change the Session ID to start a new memory thread.")
    
    if st.button("Clear Current Screen"):
        st.session_state.chat_history = []
        st.rerun()

# Display historical chat messages in the UI
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "audio" in msg:
            st.audio(msg["audio"], format="audio/mp3")

# The unified input widget accepting text, files, and microphone audio
user_submission = st.chat_input(
    "Message Jarvis...", 
    accept_audio=True, 
    accept_file=True
)

if user_submission:
    # The widget returns a dictionary containing the submission data 
    text_input = user_submission["text"]
    files = user_submission["files"]
    audio_file = user_submission["audio"]
    
    final_prompt = text_input

    # Handle Audio Input via Whisper
    if audio_file:
        with open("temp_mic.wav", "wb") as f:
            f.write(audio_file.getvalue())
        segments, _ = st.session_state.whisper.transcribe("temp_mic.wav", beam_size=5)
        transcribed_text = "".join(segment.text for segment in segments).strip()
        final_prompt = f"{final_prompt} {transcribed_text}".strip()
        os.remove("temp_mic.wav")

    # Handle File Uploads (Save locally so Jarvis tools can read them)
    if files:
        for uploaded_file in files:
            file_path = os.path.join("downloads", uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            final_prompt += f"\n[System: User uploaded a file located at {file_path}. Use the read_local_file tool to access it if needed.]"

    # Display user prompt
    if final_prompt:
        st.session_state.chat_history.append({"role": "user", "content": final_prompt})
        with st.chat_message("user"):
            st.markdown(final_prompt)

        # Generate Jarvis Response
        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                config = {"configurable": {"thread_id": thread_id}}
                result = jarvis_agent.invoke(
                    {"messages": [{"role": "user", "content": final_prompt}]},
                    config=config
                )
                
                response_text = result["messages"][-1].content
                st.markdown(response_text)
                
                # Generate TTS audio for the response
                audio_bytes = st.session_state.tts.generate_audio(response_text)
                st.audio(audio_bytes, format="audio/mp3", autoplay=True)

        # Save to history
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": response_text,
            "audio": audio_bytes
        })