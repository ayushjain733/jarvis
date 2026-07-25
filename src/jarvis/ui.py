import streamlit as st
import os
import random
from dotenv import load_dotenv
from faster_whisper import WhisperModel

import db as db
import auth as auth
from agent import jarvis_agent
from tts import TextToSpeech

load_dotenv()
db.init_db()

st.set_page_config(page_title="Jarvis OS", page_icon="🤖", layout="wide")

# Initialize Session State
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "current_thread_id" not in st.session_state:
    st.session_state.current_thread_id = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------------------------------------------------------
# AUTHENTICATION SCREEN (PURE EMAIL LOGIN/SIGNUP)
# ---------------------------------------------------------
def render_auth_page():
    st.title("🔒 Access Jarvis OS")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])
    
    # LOGIN TAB
    with tab1:
        l_email = st.text_input("Email", key="l_email")
        l_pass = st.text_input("Password", type="password", key="l_pass")
        if st.button("Login", use_container_width=True):
            uid = db.verify_user_login(l_email, l_pass)
            if uid:
                st.session_state.user_id = uid
                st.toast("Logged in successfully!", icon="✅")
                st.rerun()
            else:
                st.error("Invalid email or password.")

    # SIGN UP TAB
    with tab2:
        s_email = st.text_input("Email", key="s_email")
        s_pass = st.text_input("Password", type="password", key="s_pass")
        
        # Captcha Generation
        if "captcha_ans" not in st.session_state:
            q, a = auth.generate_captcha()
            st.session_state.captcha_q = q
            st.session_state.captcha_ans = a
            
        captcha_input = st.text_input(f"Verify you are human: {st.session_state.captcha_q}")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Send OTP", use_container_width=True):
                if not auth.is_valid_email(s_email):
                    st.error("Please use a trusted email provider (Gmail, Yahoo, Outlook, etc.).")
                elif captcha_input != st.session_state.captcha_ans:
                    st.error("Incorrect captcha answer. Try again.")
                else:
                    otp = str(random.randint(100000, 999999))
                    st.session_state.pending_otp = otp
                    
                    success, msg = auth.send_verification_email(s_email, otp)
                    if success:
                        st.session_state.otp_msg = msg
                        st.toast("OTP processed!", icon="📩")
                    else:
                        st.error(msg)

        # Show OTP Status / Dev mode notification
        if "otp_msg" in st.session_state:
            st.info(st.session_state.otp_msg)
                
        otp_input = st.text_input("Enter 6-digit OTP", key="otp_input")
        if st.button("Create Account", use_container_width=True):
            if otp_input and otp_input == st.session_state.get("pending_otp"):
                uid = db.create_user(s_email, s_pass)
                if uid:
                    st.success("Account created successfully! You can now log in.")
                else:
                    st.error("Account already exists with this email.")
            else:
                st.error("Invalid OTP code. Please check and try again.")

# ---------------------------------------------------------
# MAIN APPLICATION INTERFACE
# ---------------------------------------------------------
def render_main_app():
    if "whisper" not in st.session_state:
        st.session_state.whisper = WhisperModel("base", device="cpu", compute_type="int8")
    if "tts" not in st.session_state:
        st.session_state.tts = TextToSpeech()

    with st.sidebar:
        st.header("Jarvis System")
        if st.button("➕ New Chat", use_container_width=True):
            new_id = db.create_thread(st.session_state.user_id, "New Chat")
            st.session_state.current_thread_id = new_id
            st.session_state.chat_history = []
            st.rerun()
            
        st.divider()
        st.subheader("History")
        
        threads = db.get_user_threads(st.session_state.user_id)
        for t in threads:
            col1, col2 = st.columns([0.85, 0.15])
            with col1:
                if st.button(f"💬 {t['title']}", key=f"load_{t['id']}", use_container_width=True):
                    st.session_state.current_thread_id = t['id']
                    st.session_state.chat_history = []
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_{t['id']}"):
                    db.delete_thread(t['id'])
                    if st.session_state.current_thread_id == t['id']:
                        st.session_state.current_thread_id = None
                    st.rerun()
                    
        st.divider()
        if st.button("Log Out", use_container_width=True):
            st.session_state.user_id = None
            st.session_state.current_thread_id = None
            st.rerun()

    if not st.session_state.current_thread_id:
        st.title("🤖 Welcome to Jarvis OS")
        st.caption("Click '➕ New Chat' in the sidebar to start a session.")
        return

    st.title("🤖 Jarvis Terminal")

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "audio" in msg:
                st.audio(msg["audio"], format="audio/mp3")

    user_submission = st.chat_input("Command Jarvis...", accept_audio=True, accept_file=True)

    if user_submission:
        text_input = user_submission["text"]
        files = user_submission["files"]
        audio = user_submission["audio"]
        final_prompt = text_input

        if audio:
            with open("temp_mic.wav", "wb") as f:
                f.write(audio.getvalue())
            segments, _ = st.session_state.whisper.transcribe("temp_mic.wav", beam_size=5)
            final_prompt = f"{final_prompt} " + "".join(s.text for s in segments).strip()
            os.remove("temp_mic.wav")

        if files:
            os.makedirs("downloads", exist_ok=True)
            for uploaded_file in files:
                file_path = os.path.join("downloads", uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                final_prompt += f"\n[System: Uploaded file saved at {file_path}. Use read_local_file tool if needed.]"

        if len(st.session_state.chat_history) == 0 and final_prompt:
            short_title = final_prompt[:25] + "..." if len(final_prompt) > 25 else final_prompt
            db.update_thread_title(st.session_state.current_thread_id, short_title)

        st.session_state.chat_history.append({"role": "user", "content": final_prompt})
        with st.chat_message("user"):
            st.markdown(final_prompt)

        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                config = {"configurable": {"thread_id": st.session_state.current_thread_id}}
                result = jarvis_agent.invoke(
                    {"messages": [{"role": "user", "content": final_prompt}]},
                    config=config
                )
                
                response_text = result["messages"][-1].content
                st.markdown(response_text)
                
                audio_bytes = st.session_state.tts.generate_audio(response_text)
                st.audio(audio_bytes, format="audio/mp3", autoplay=True)

        st.session_state.chat_history.append({
            "role": "assistant", "content": response_text, "audio": audio_bytes
        })

# Router
if st.session_state.user_id is None:
    render_auth_page()
else:
    render_main_app()