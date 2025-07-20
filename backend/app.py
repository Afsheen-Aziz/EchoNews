import streamlit as st
import requests
import re
import os
import time
import tempfile
import queue
from gtts import gTTS
import speech_recognition as sr
from datetime import datetime

# --- CONFIG ---
st.set_page_config(
    page_title="EchoNews - AI-Powered News Assistant",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS ---
st.markdown("""
<style>
body, * { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%); min-height: 100vh; }
.main-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2.5rem; border-radius: 15px; color: white; text-align: center; margin-bottom: 2rem; box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);}
.news-card { background: linear-gradient(145deg, #ffffff 0%, #fafbfc 100%); padding: 1.8rem; border-radius: 12px; border-left: 5px solid #007bff; margin: 1.5rem 0; box-shadow: 0 4px 16px rgba(0,0,0,0.1);}
.news-card:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(0,0,0,0.15);}
.status-success { background: #d4edda; color: #155724; border-left: 4px solid #28a745; padding: 1rem; border-radius: 10px; margin: 1rem 0;}
.status-error { background: #f8d7da; color: #721c24; border-left: 4px solid #dc3545; padding: 1rem; border-radius: 10px; margin: 1rem 0;}
.status-listening { background: #e3e7fd; color: #667eea; border-left: 4px solid #667eea; padding: 1rem; border-radius: 10px; margin: 1rem 0;}
.bookmark-card { background: #fffbe6; color: #856404; border-left: 4px solid #ffc107; padding: 1rem; border-radius: 10px; margin: 1rem 0;}
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
for key, default in {
    'current_news': None,
    'audio_playing': False,
    'user_question': "",
    'aspirant_mode': False,
    'bookmarks': [],
    'current_language': "en",
    'user_interests': [],
    'interests_set': False,
    'current_news_text': "",
    'paused_news_text': "",
    'is_playing_audio': False,
    'echo_detected': False,
    'new_query': "",
    'echo_count': 0,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- NEWS API ---
NEWS_API_KEY = "pub_de86554e677043f7b7c83b1bfb7f4a9b"  # Free key from newsdata.io
NEWS_URL = "https://newsdata.io/api/1/news"
LATEST_NEWS_URL = "https://newsdata.io/api/1/latest"

AVAILABLE_TOPICS = {
    "Technology": {"icon": "💻", "description": "Latest in tech, AI, and innovation"},
    "Business": {"icon": "💼", "description": "Market trends and business news"},
    "Science": {"icon": "🔬", "description": "Scientific discoveries and research"},
    "Health": {"icon": "🏥", "description": "Medical breakthroughs and wellness"},
    "Sports": {"icon": "⚽", "description": "Sports events and athletic achievements"},
    "Entertainment": {"icon": "🎬", "description": "Movies, music, and celebrity news"},
    "Politics": {"icon": "🏛️", "description": "Political developments and policies"},
    "Environment": {"icon": "🌍", "description": "Climate change and environmental news"},
    "Education": {"icon": "📚", "description": "Learning and academic developments"},
    "Space": {"icon": "🚀", "description": "Space exploration and astronomy"}
}

# --- HELPERS ---
def fetch_news(topic):
    params = {'q': topic, 'language': 'en', 'apikey': NEWS_API_KEY, 'size': 3}
    response = requests.get(NEWS_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        articles = data.get("results", [])
        if articles:
            summary = "\n\n".join([f"🔹 {a.get('title', 'No title')} - {a.get('description', 'No description')}" for a in articles])
            return summary, articles
        return "No news found on this topic.", []
    return f"Failed to fetch news. Error: {response.status_code}", []

def fetch_latest_news():
    params = {'language': 'en', 'apikey': NEWS_API_KEY, 'size': 5}
    response = requests.get(LATEST_NEWS_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        articles = data.get("results", [])
        if articles:
            summary = "\n\n".join([f"🔹 {a.get('title', 'No title')} - {a.get('description', 'No description')}" for a in articles])
            return summary, articles
        return "No latest news available.", []
    return f"Failed to fetch latest news. Error: {response.status_code}", []

def fetch_latest_news_for_interests():
    if not st.session_state.user_interests:
        return "Please select your interests first to get personalized news.", []
    all_news = []
    all_articles = []
    for topic in st.session_state.user_interests:
        params = {'q': topic, 'language': 'en', 'apikey': NEWS_API_KEY, 'size': 2}
        response = requests.get(NEWS_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            articles = data.get("results", [])
            if articles:
                topic_news = f"\n📰 **{topic} News:**\n"
                topic_news += "\n".join([f"🔹 {a.get('title', 'No title')} - {a.get('description', 'No description')}" for a in articles[:2]])
                all_news.append(topic_news)
                all_articles.extend(articles[:2])
    if all_news:
        return "\n\n".join(all_news), all_articles
    return "No news found for your selected interests.", []

def speak_text(text):
    tts = gTTS(text)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        st.session_state.is_playing_audio = True
        st.audio(fp.name, format="audio/mp3")
        st.session_state.is_playing_audio = False

def listen_to_user():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.markdown('<div class="status-listening">🎙️ Listening... Please speak.</div>', unsafe_allow_html=True)
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            st.markdown(f'<div class="status-success">✅ You said: <strong>{text}</strong></div>', unsafe_allow_html=True)
            return text
        except sr.UnknownValueError:
            st.markdown('<div class="status-error">❌ Could not understand your speech.</div>', unsafe_allow_html=True)
        except sr.RequestError:
            st.markdown('<div class="status-error">⚠️ Error with speech recognition service.</div>', unsafe_allow_html=True)
    return ""

def is_general_question(text):
    return bool(re.search(r"\b(what|who|when|where|why|how|explain|define)\b", text.lower())) or "?" in text

def is_latest_news_request(text):
    latest_keywords = ['latest', 'recent', 'current', 'today', 'news', 'update']
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in latest_keywords)

def create_chat_bubble(content, is_ai=False):
    if is_ai:
        return f"""
        <div class="news-card" style="margin-left: 3rem;">
            <div style="display: flex; align-items: flex-start;">
                <div style="font-size:2rem;margin-right:1rem;">🤖</div>
                <div style="flex: 1;">{content}</div>
            </div>
        </div>
        """
    else:
        return f"""
        <div class="news-card" style="margin-right: 3rem; background: #e3e7fd;">
            <div style="display: flex; align-items: flex-start;">
                <div style="flex: 1; text-align: right;">{content}</div>
                <div style="font-size:2rem;margin-left:1rem;">👤</div>
            </div>
        </div>
        """

# --- HEADER ---
st.markdown("""
<div class="main-header">
    <h1>🎙️ EchoNews - AI-Powered News Assistant</h1>
    <p>Your Voice-Controlled AI News Assistant</p>
    <p style="color: rgba(255,255,255,0.7); font-size: 1rem;">
        Choose your interests and ask for topics or questions like <i>What is quantum computing?</i>
    </p>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🎛️ Settings")
    language = st.selectbox("Select Language", ["English", "Malayalam"], index=0)
    st.session_state.current_language = "en" if language == "English" else "ml"
    aspirant_mode = st.checkbox("Enable UPSC/PSC Mode", value=st.session_state.aspirant_mode)
    st.session_state.aspirant_mode = aspirant_mode
    if aspirant_mode:
        st.markdown("""
        <div class="news-card" style="background: #ff6b6b; color: white;">
            <h4>🎯 UPSC/PSC Features:</h4>
            <ul>
                <li>Daily current affairs</li>
                <li>MCQ quizzes</li>
                <li>Bookmarks</li>
                <li>Date-wise news</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    if st.session_state.bookmarks:
        st.markdown("#### 🔖 Bookmarks")
        for i, bookmark in enumerate(st.session_state.bookmarks):
            st.markdown(f"""
            <div class="bookmark-card">
                <b>{bookmark.get('title', bookmark)[:60]}</b>
                <br>
                <small>{bookmark.get('description', '')}</small>
            </div>
            """, unsafe_allow_html=True)

# --- INTEREST SELECTION ---
if not st.session_state.interests_set:
    st.markdown("### 🎯 Select Your Interests (up to 5)")
    selected = st.multiselect(
        "Choose topics for personalized news:",
        list(AVAILABLE_TOPICS.keys()),
        default=st.session_state.user_interests,
        help="Select up to 5 topics"
    )
    if len(selected) > 5:
        st.warning("You can select up to 5 interests only.")
    else:
        st.session_state.user_interests = selected
    if st.button("Save Interests"):
        if st.session_state.user_interests:
            st.session_state.interests_set = True
            st.success("Interests saved! You can now get personalized news.")
        else:
            st.warning("Please select at least one interest.")
    st.stop()

# --- TABS ---
tab1, tab2, tab3, tab4 = st.tabs(["📰 News", "🎧 Audio", "❓ Q&A", "🎯 Aspirant Mode"])

# --- TAB 1: NEWS ---
with tab1:
    st.markdown("### 📰 Latest News")
    news, articles = fetch_latest_news()
    st.markdown(news)
    st.markdown("### 🔎 Search News by Topic")
    topic = st.selectbox("Choose a topic", list(AVAILABLE_TOPICS.keys()))
    if st.button("Fetch News", key="fetch_topic_news"):
        summary, topic_articles = fetch_news(topic)
        st.markdown(create_chat_bubble(summary, is_ai=True), unsafe_allow_html=True)
        if st.button("🔊 Listen to this news", key="listen_topic_news"):
            speak_text(summary)
        if st.button("📌 Bookmark this news", key="bookmark_topic_news"):
            if topic_articles:
                st.session_state.bookmarks.append(topic_articles[0])
            else:
                st.session_state.bookmarks.append({"title": summary, "description": ""})
            st.success("Bookmarked!")

# --- TAB 2: AUDIO/VOICE ---
with tab2:
    st.markdown("### 🎤 Voice News & Q&A")
    st.markdown("Tap below and speak your news topic or question.")
    if st.button("🎤 Tap to Speak", key="voice_input_btn"):
        user_input = listen_to_user()
        if user_input:
            st.markdown(create_chat_bubble(user_input, is_ai=False), unsafe_allow_html=True)
            if is_latest_news_request(user_input):
                latest_news, _ = fetch_latest_news_for_interests()
                st.session_state.current_news_text = latest_news
                st.markdown(create_chat_bubble(latest_news, is_ai=True), unsafe_allow_html=True)
                speak_text(latest_news)
            elif is_general_question(user_input):
                st.markdown(create_chat_bubble("Sorry, AI Q&A is not enabled in this demo.", is_ai=True), unsafe_allow_html=True)
            else:
                summary, _ = fetch_news(user_input)
                st.session_state.current_news_text = summary
                st.markdown(create_chat_bubble(summary, is_ai=True), unsafe_allow_html=True)
                speak_text(summary)

# --- TAB 3: Q&A ---
with tab3:
    st.markdown("### ❓ Ask a Question")
    question = st.text_area("Enter your question:", height=100)
    if st.button("🔍 Get Answer", key="qa_btn"):
        if question:
            st.markdown(create_chat_bubble("Sorry, AI Q&A is not enabled in this demo.", is_ai=True), unsafe_allow_html=True)
        else:
            st.warning("Please enter a question.")

# --- TAB 4: Aspirant Mode ---
with tab4:
    if st.session_state.aspirant_mode:
        st.markdown("### 🎯 Aspirant Mode - UPSC/PSC Preparation")
        st.markdown("#### 📅 Daily Current Affairs")
        selected_date = st.date_input(
            "Select Date:",
            value=datetime.now().date(),
            max_value=datetime.now().date()
        )
        # Just fetch latest news for the selected date (mock, as API doesn't support date filter in free tier)
        st.info("Showing latest news for selected date (demo, not date-filtered).")
        news, articles = fetch_latest_news()
        for i, art in enumerate(articles):
            st.markdown(f"""
            <div class="news-card">
                <h4>{i+1}. {art.get('title','')}</h4>
                <p><strong>Category:</strong> General | <strong>Date:</strong> {selected_date}</p>
                <p>{art.get('description','')}</p>
                <p><strong>Relevance to UPSC:</strong> General Awareness</p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("#### 🧠 Smart Quiz")
        if st.button("🎯 Generate Quiz", key="quiz_btn"):
            st.info("Quiz generation feature coming soon!")
            st.markdown("""
            <div class="news-card">
                <h4>Sample MCQ:</h4>
                <p><strong>Q:</strong> What is the capital of India?</p>
                <ul>
                    <li>A) Mumbai</li>
                    <li>B) Delhi</li>
                    <li>C) Kolkata</li>
                    <li>D) Chennai</li>
                </ul>
                <p><strong>Answer:</strong> B) Delhi</p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("#### 🎧 Daily Summary Podcast")
        if st.button("🎙️ Generate Daily Podcast", key="podcast_btn"):
            st.info("Daily podcast generation feature coming soon!")
    else:
        st.markdown("### 🎯 Enable Aspirant Mode")
        st.info("Please enable Aspirant Mode in the sidebar to access UPSC/PSC features.")

# --- FOOTER ---
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6c757d; padding: 1rem;">
    <p>📰 EchoNews - AI-Powered News Assistant | Built with ❤️ using Streamlit</p>
</div>
""", unsafe_allow_html=True)