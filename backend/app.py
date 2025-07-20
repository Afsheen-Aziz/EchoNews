import streamlit as st
import requests
import re
import os
import time
import tempfile
from gtts import gTTS
import speech_recognition as sr
from datetime import datetime
import random

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
    'interest_news_generated': False,
    'topic_news_generated': False,
    'last_interest_news': "",
    'last_interest_articles': [],
    'last_topic_news': "",
    'last_topic_articles': [],
    'audio_result': "",
    'quiz_questions': [],
    'quiz_answers': [],
    'quiz_user_answers': [],
    'quiz_show_result': False,
    'quiz_options': [],
    'quiz_active': False,
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

def clean_text_for_tts(text):
    text = re.sub(r'[^\w\s.,;:!?\'\"-]', '', text, flags=re.UNICODE)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_audio_bytes(text):
    clean = clean_text_for_tts(text)
    tts = gTTS(clean)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        with open(fp.name, "rb") as f:
            audio_bytes = f.read()
    os.remove(fp.name)
    return audio_bytes

def audio_with_optional_text(text, key_prefix):
    audio_bytes = get_audio_bytes(text)
    st.audio(audio_bytes, format="audio/mp3")
    show_text = st.checkbox("Show Text", key=f"{key_prefix}_show_text")
    if show_text:
        st.markdown(f"<div class='news-card'>{text}</div>", unsafe_allow_html=True)

def speak_text(text):
    audio_bytes = get_audio_bytes(text)
    st.session_state.is_playing_audio = True
    st.audio(audio_bytes, format="audio/mp3")
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

def extract_entity_simple(text):
    words = re.findall(r'\b[A-Z][a-z]+\b', text)
    numbers = re.findall(r'\b\d{4}\b', text)
    if words:
        return words[0]
    if numbers:
        return numbers[0]
    months = re.findall(r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\b', text)
    if months:
        return months[0]
    return None

def generate_quiz_from_articles(articles, num_questions=3):
    questions = []
    options = []
    answers = []
    entities = []
    for art in articles:
        title = art.get('title') or ''
        desc = art.get('description') or ''
        ent = extract_entity_simple(title + " " + desc)
        entities.append(ent)
    for i, art in enumerate(articles[:num_questions]):
        title = art.get('title') or ''
        desc = art.get('description') or ''
        ent = extract_entity_simple(title + " " + desc)
        if ent and ent in (desc or title):
            q = f"<b>Which key person/place/number is mentioned in today's news?</b>"
            correct = ent
            distractors = [e for j, e in enumerate(entities) if e and j != i]
            distractors = random.sample(distractors, min(3, len(distractors)))
            opts = [correct] + distractors
            random.shuffle(opts)
            questions.append(q)
            options.append(opts)
            answers.append(correct)
        else:
            q = f"<b>What is the main topic of one of today's news items?</b>"
            correct = title.split()[0] if title else "News"
            distractors = [ (a.get('title') or '').split()[0] for a in articles if (a.get('title') or '') != title]
            distractors = random.sample(distractors, min(3, len(distractors)))
            opts = [correct] + distractors
            random.shuffle(opts)
            questions.append(q)
            options.append(opts)
            answers.append(correct)
    return questions, options, answers

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
    audio_with_optional_text(news, "latest_news")

    # --- Personalized News by Interests ---
    st.markdown("### 🌟 Personalized News (Based on Your Interests)")
    if st.button("📰 Generate News for My Interests", key="interest_news_btn"):
        summary, interest_articles = fetch_latest_news_for_interests()
        st.session_state['last_interest_news'] = summary
        st.session_state['last_interest_articles'] = interest_articles
        st.session_state['interest_news_generated'] = True

    if st.session_state.get('interest_news_generated'):
        audio_with_optional_text(st.session_state['last_interest_news'], "interest_news")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔊 Listen to this news", key="listen_interest_news"):
                speak_text(st.session_state['last_interest_news'])
        with col2:
            if st.button("📌 Bookmark this news", key="bookmark_interest_news"):
                if st.session_state.get('last_interest_articles'):
                    st.session_state.bookmarks.append(st.session_state['last_interest_articles'][0])
                else:
                    st.session_state.bookmarks.append({"title": st.session_state['last_interest_news'], "description": ""})
                st.success("Bookmarked!")

    # --- Search News by Topic ---
    st.markdown("### 🔎 Search News by Topic")
    topic = st.selectbox("Choose a topic", list(AVAILABLE_TOPICS.keys()))
    if st.button("Fetch News", key="fetch_topic_news"):
        summary, topic_articles = fetch_news(topic)
        st.session_state['last_topic_news'] = summary
        st.session_state['last_topic_articles'] = topic_articles
        st.session_state['topic_news_generated'] = True

    if st.session_state.get('topic_news_generated'):
        audio_with_optional_text(st.session_state['last_topic_news'], "topic_news")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔊 Listen to this news", key="listen_topic_news"):
                speak_text(st.session_state['last_topic_news'])
        with col2:
            if st.button("📌 Bookmark this news", key="bookmark_topic_news"):
                if st.session_state.get('last_topic_articles'):
                    st.session_state.bookmarks.append(st.session_state['last_topic_articles'][0])
                else:
                    st.session_state.bookmarks.append({"title": st.session_state['last_topic_news'], "description": ""})
                st.success("Bookmarked!")

# --- TAB 2: AUDIO/VOICE ---
with tab2:
    st.markdown("### 🎤 Voice News & Q&A")
    st.markdown("Tap below and speak your news topic or question.")

    # Only update audio_result when button is pressed
    if st.button("🎤 Tap to Speak", key="voice_input_btn"):
        user_input = listen_to_user()
        if user_input:
            st.markdown(create_chat_bubble(user_input, is_ai=False), unsafe_allow_html=True)
            if is_latest_news_request(user_input):
                latest_news, _ = fetch_latest_news_for_interests()
                st.session_state.audio_result = latest_news
            elif is_general_question(user_input):
                st.session_state.audio_result = "Sorry, AI Q&A is not enabled in this demo."
            else:
                summary, _ = fetch_news(user_input)
                st.session_state.audio_result = summary

    # Always show the last result (audio + checkbox) if it exists
    if st.session_state.audio_result:
        audio_with_optional_text(st.session_state.audio_result, "voice_audio_result")

# --- TAB 3: Q&A ---
with tab3:
    st.markdown("### ❓ Ask a Question")
    question = st.text_area("Enter your question:", height=100)
    if st.button("🔍 Get Answer", key="qa_btn"):
        if question:
            audio_with_optional_text("Sorry, AI Q&A is not enabled in this demo.", "qa_tab")
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
        st.info("Showing latest news for selected date (demo, not date-filtered).")
        news, articles = fetch_latest_news()

        # Quiz state
        quiz_active = st.session_state.get("quiz_active", False)

        # Only show headlines if quiz is not active
        if not quiz_active:
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
        if not quiz_active and st.button("🎯 Generate Quiz", key="quiz_btn"):
            questions, options, answers = generate_quiz_from_articles(articles)
            st.session_state.quiz_questions = questions
            st.session_state.quiz_answers = answers
            st.session_state.quiz_options = options
            st.session_state.quiz_user_answers = [None] * len(questions)
            st.session_state.quiz_show_result = False
            st.session_state.quiz_active = True

        if st.session_state.get("quiz_active"):
            for idx, q in enumerate(st.session_state.quiz_questions):
                st.markdown(f"**Q{idx+1}:** {q}", unsafe_allow_html=True)
                st.session_state.quiz_user_answers[idx] = st.radio(
                    f"Select answer for Q{idx+1}",
                    st.session_state.quiz_options[idx],
                    key=f"quiz_radio_{idx}"
                )
            if st.button("Submit Quiz", key="submit_quiz_btn"):
                st.session_state.quiz_show_result = True

        if st.session_state.get("quiz_show_result"):
            correct = 0
            for idx, user_ans in enumerate(st.session_state.quiz_user_answers):
                if user_ans == st.session_state.quiz_answers[idx]:
                    correct += 1
            st.success(f"You got {correct} out of {len(st.session_state.quiz_questions)} correct!")
            if st.button("Reset Quiz", key="reset_quiz_btn"):
                st.session_state.quiz_questions = []
                st.session_state.quiz_answers = []
                st.session_state.quiz_options = []
                st.session_state.quiz_user_answers = []
                st.session_state.quiz_show_result = False
                st.session_state.quiz_active = False

        st.markdown("#### 🎧 Daily Summary Podcast")
        if st.button("🎙️ Generate Daily Podcast", key="podcast_btn"):
            podcast_text = "Here are today's top headlines. " + " ".join([a.get('title', '') or '' for a in articles])
            speak_text(podcast_text)
            st.info("Playing today's headlines as a podcast.")
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