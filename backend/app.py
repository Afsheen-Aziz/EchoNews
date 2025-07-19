import streamlit as st
import speech_recognition as sr
import pyttsx3
import requests

# Set up Streamlit page
st.set_page_config(page_title="EchoNews", layout="centered")

# Text-to-Speech engine
engine = pyttsx3.init()

# Your NewsAPI key
API_KEY = "617cd71043ad4eedb9be05dfbd4f1aed"
NEWS_URL = "https://newsapi.org/v2/everything"

# Function to fetch real news from NewsAPI
def fetch_news(topic):
    params = {
        'q': topic,
        'sortBy': 'publishedAt',
        'language': 'en',
        'apiKey': API_KEY,
        'pageSize': 3  # limit to top 3 articles
    }
    response = requests.get(NEWS_URL, params=params)
    if response.status_code == 200:
        articles = response.json().get("articles", [])
        if articles:
            # Summarize top articles (titles + description)
            summary = "\n\n".join(
                [f"🔹 {a['title']} - {a['description'] or ''}" for a in articles]
            )
            return summary
        else:
            return "No news found on this topic."
    else:
        return "Failed to fetch news. Please try again later."

# Function to get speech input from mic
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

# Title UI
st.markdown(
    """
    <div style="text-align: center;">
        <h1>🎙️ EchoNews - Voice Controlled News App</h1>
        <p>Ask for a topic like: <b>Technology</b>, <b>Sports</b>, or <b>Politics</b></p>
    </div>
    """, unsafe_allow_html=True
)

# Main button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🎤 Tap to Speak"):
        topic = listen_to_user()
        if topic:
            summary = fetch_news(topic)
            st.subheader("📰 News Summary:")
            st.write(summary)
            engine.say(summary)
            engine.runAndWait()
