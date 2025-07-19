import streamlit as st
import speech_recognition as sr
import requests
import re
from dotenv import load_dotenv
import os
from gtts import gTTS
import tempfile
from genai_helper import ask_gemini
# Load environment variables
load_dotenv()

# Streamlit config
st.set_page_config(page_title="EchoNews", layout="centered")

# News API
NEWS_API_KEY = "617cd71043ad4eedb9be05dfbd4f1aed"
NEWS_URL = "https://newsapi.org/v2/everything"

# Title
st.markdown("""
    <div style="text-align: center;">
        <h1>🎙️ EchoNews - Voice Controlled News App</h1>
        <p>Ask for a topic like: <b>Technology</b>, or a question like: <i>What is quantum computing?</i></p>
    </div>
""", unsafe_allow_html=True)

# Helpers
def fetch_news(topic):
    params = {
        'q': topic,
        'sortBy': 'publishedAt',
        'language': 'en',
        'apiKey': NEWS_API_KEY,
        'pageSize': 3
    }
    response = requests.get(NEWS_URL, params=params)
    if response.status_code == 200:
        articles = response.json().get("articles", [])
        if articles:
            summary = "\n\n".join([f"🔹 {a['title']} - {a['description'] or ''}" for a in articles])
            return summary
        return "No news found on this topic."
    return "Failed to fetch news. Please try again later."

def speak_text(text):
    tts = gTTS(text)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        st.audio(fp.name, format="audio/mp3")

def listen_to_user():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎙️ Listening... Please speak.")
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            st.success(f"✅ You said: **{text}**")
            return text
        except sr.UnknownValueError:
            st.error("❌ Could not understand your speech.")
        except sr.RequestError:
            st.error("⚠️ Error with speech recognition service.")
    return ""

def is_general_question(text):
    return bool(re.search(r"\b(what|who|when|where|why|how|explain|define)\b", text.lower())) or "?" in text


    # To integrate Gemini later, call Google GenAI API here

# Main UI
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🎤 Tap to Speak", key="main_button"):
        user_input = listen_to_user()

        if user_input:
            if is_general_question(user_input):
                st.subheader("🤖 Gemini Answer:")
                answer = ask_gemini(user_input)
                st.write(answer)
                speak_text(answer)

                if 'last_topic' in st.session_state:
                    st.subheader("🔁 Resuming News:")
                    summary = fetch_news(st.session_state['last_topic'])
                    st.write(summary)
                    speak_text(summary)

            else:
                st.session_state['last_topic'] = user_input
                summary = fetch_news(user_input)
                st.subheader("📰 News Summary:")
                st.write(summary)
                speak_text(summary)
                
            answer = ask_gemini(user_input)                

