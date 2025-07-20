import streamlit as st
import speech_recognition as sr
import requests
import re
from dotenv import load_dotenv
import os
from gtts import gTTS
import tempfile
try:
    from genai_helper import ask_gemini
except ImportError:
    from backend.genai_helper import ask_gemini
import time
import threading
import queue

# Load environment variables
load_dotenv()

# Streamlit config
st.set_page_config(
    page_title="EchoNews", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for modern Gemini-inspired design
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Global styles */
* {
    font-family: 'Inter', sans-serif;
}

/* Background with gradient */
.stApp {
    background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
    min-height: 100vh;
}

/* Hide default Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Glassmorphism card */
.glass-card {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    border-radius: 24px;
    padding: 2rem;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    margin: 1rem 0;
}

/* Modern button styling */
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    border-radius: 50px;
    color: white;
    font-weight: 600;
    padding: 1rem 2rem;
    font-size: 1.1rem;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    position: relative;
    overflow: hidden;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
}

/* Pulsing animation for mic button */
@keyframes pulse {
    0% { transform: scale(1); box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4); }
    50% { transform: scale(1.05); box-shadow: 0 8px 25px rgba(102, 126, 234, 0.8); }
    100% { transform: scale(1); box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4); }
}

.pulse-animation {
    animation: pulse 2s infinite;
}

/* Chat bubble styling */
.chat-bubble {
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    padding: 1.5rem;
    margin: 1rem 0;
    border-left: 4px solid #667eea;
    position: relative;
}

.chat-bubble::before {
    content: '';
    position: absolute;
    left: -10px;
    top: 20px;
    width: 0;
    height: 0;
    border: 10px solid transparent;
    border-right-color: rgba(255, 255, 255, 0.1);
}

/* AI avatar */
.ai-avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 1rem;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

/* Waveform animation */
@keyframes waveform {
    0%, 100% { height: 5px; }
    50% { height: 20px; }
}

.waveform {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 3px;
    margin: 1rem 0;
}

.waveform-bar {
    width: 3px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 2px;
    animation: waveform 1.5s ease-in-out infinite;
}

.waveform-bar:nth-child(1) { animation-delay: 0s; }
.waveform-bar:nth-child(2) { animation-delay: 0.1s; }
.waveform-bar:nth-child(3) { animation-delay: 0.2s; }
.waveform-bar:nth-child(4) { animation-delay: 0.3s; }
.waveform-bar:nth-child(5) { animation-delay: 0.4s; }
.waveform-bar:nth-child(6) { animation-delay: 0.5s; }
.waveform-bar:nth-child(7) { animation-delay: 0.6s; }

/* Modern title styling */
.modern-title {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 3rem;
    font-weight: 700;
    text-align: center;
    margin-bottom: 1rem;
}

.modern-subtitle {
    color: rgba(255, 255, 255, 0.8);
    text-align: center;
    font-size: 1.2rem;
    margin-bottom: 2rem;
}

/* Status indicators */
.status-listening {
    background: rgba(102, 126, 234, 0.2);
    border: 1px solid rgba(102, 126, 234, 0.5);
    border-radius: 12px;
    padding: 1rem;
    margin: 1rem 0;
    text-align: center;
    color: #667eea;
}

.status-success {
    background: rgba(34, 197, 94, 0.2);
    border: 1px solid rgba(34, 197, 94, 0.5);
    border-radius: 12px;
    padding: 1rem;
    margin: 1rem 0;
    color: #22c55e;
}

.status-error {
    background: rgba(239, 68, 68, 0.2);
    border: 1px solid rgba(239, 68, 68, 0.5);
    border-radius: 12px;
    padding: 1rem;
    margin: 1rem 0;
    color: #ef4444;
}

.status-echo {
    background: rgba(245, 158, 11, 0.2);
    border: 1px solid rgba(245, 158, 11, 0.5);
    border-radius: 12px;
    padding: 1rem;
    margin: 1rem 0;
    text-align: center;
    color: #f59e0b;
    animation: pulse 1s infinite;
}

.status-continuous {
    background: rgba(102, 126, 234, 0.15);
    border: 2px solid rgba(102, 126, 234, 0.6);
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1rem 0;
    text-align: center;
    color: #667eea;
    position: relative;
    overflow: hidden;
}

.status-continuous::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(102, 126, 234, 0.2), transparent);
    animation: shimmer 2s infinite;
}

@keyframes shimmer {
    0% { left: -100%; }
    100% { left: 100%; }
}

/* Continuous listening button styles */
.continuous-btn {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border: none;
    border-radius: 50px;
    color: white;
    font-weight: 600;
    padding: 1rem 2rem;
    font-size: 1rem;
    transition: all 0.3s ease;
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    position: relative;
    overflow: hidden;
}

.continuous-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
}

.continuous-btn.active {
    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
    box-shadow: 0 4px 15px rgba(34, 197, 94, 0.4);
}

.continuous-btn.stop {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    box-shadow: 0 4px 15px rgba(239, 68, 68, 0.4);
}

/* Instructions box */
.instructions-box {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 1.5rem;
    margin: 2rem 0;
}

.instructions-box h4 {
    color: #667eea;
    margin-bottom: 1rem;
    font-weight: 600;
}

.instructions-box ul {
    color: rgba(255, 255, 255, 0.8);
    line-height: 1.6;
    margin: 0;
    padding-left: 1.5rem;
}

.instructions-box li {
    margin-bottom: 0.5rem;
}

.instructions-box strong {
    color: rgba(255, 255, 255, 0.9);
}

/* Section headers */
.section-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 1.5rem;
    font-weight: 600;
    margin: 1rem 0;
}

/* Audio player styling */
.stAudio {
    margin: 1rem 0;
}

.stAudio > div {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 0.5rem;
}

/* Topic selection styling */
.topic-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
}

.topic-card {
    background: rgba(255, 255, 255, 0.05);
    border: 2px solid rgba(255, 255, 255, 0.1);
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.topic-card:hover {
    transform: translateY(-2px);
    border-color: rgba(102, 126, 234, 0.5);
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2);
}

.topic-card.selected {
    background: rgba(102, 126, 234, 0.2);
    border-color: #667eea;
    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

.topic-card.selected::before {
    content: '✓';
    position: absolute;
    top: 10px;
    right: 10px;
    background: #667eea;
    color: white;
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;
    font-weight: bold;
}

.topic-icon {
    font-size: 2rem;
    margin-bottom: 0.5rem;
}

.topic-name {
    color: rgba(255, 255, 255, 0.9);
    font-weight: 600;
    font-size: 1rem;
}

.topic-description {
    color: rgba(255, 255, 255, 0.6);
    font-size: 0.9rem;
    margin-top: 0.5rem;
}

/* Responsive design */
@media (max-width: 768px) {
    .modern-title {
        font-size: 2rem;
    }
    .glass-card {
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .topic-grid {
        grid-template-columns: 1fr;
    }
}
</style>
""", unsafe_allow_html=True)

# News API
NEWS_API_KEY = "pub_de86554e677043f7b7c83b1bfb7f4a9b"
NEWS_URL = "https://newsdata.io/api/1/news"
LATEST_NEWS_URL = "https://newsdata.io/api/1/latest"

# Available topics with icons and descriptions
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

# Initialize session state
if 'user_interests' not in st.session_state:
    st.session_state.user_interests = []
if 'interests_set' not in st.session_state:
    st.session_state.interests_set = False

# Initialize session state for continuous listening
if 'continuous_listening' not in st.session_state:
    st.session_state.continuous_listening = False
if 'listening_thread' not in st.session_state:
    st.session_state.listening_thread = None
if 'audio_queue' not in st.session_state:
    st.session_state.audio_queue = queue.Queue()
if 'current_news_text' not in st.session_state:
    st.session_state.current_news_text = ""
if 'paused_news_text' not in st.session_state:
    st.session_state.paused_news_text = ""
if 'is_playing_audio' not in st.session_state:
    st.session_state.is_playing_audio = False
if 'echo_detected' not in st.session_state:
    st.session_state.echo_detected = False
if 'new_query' not in st.session_state:
    st.session_state.new_query = ""
if 'listening_start_time' not in st.session_state:
    st.session_state.listening_start_time = None
if 'total_listening_time' not in st.session_state:
    st.session_state.total_listening_time = 0
if 'echo_count' not in st.session_state:
    st.session_state.echo_count = 0
if 'microphone_available' not in st.session_state:
    st.session_state.microphone_available = True
if 'microphone_error' not in st.session_state:
    st.session_state.microphone_error = None

# Modern title
st.markdown("""
    <div class="glass-card">
        <h1 class="modern-title">🎙️ EchoNews</h1>
        <p class="modern-subtitle">Your Voice-Controlled AI News Assistant</p>
        <p style="text-align: center; color: rgba(255, 255, 255, 0.7); font-size: 1rem;">
            Choose your interests and ask for topics or questions like <i>What is quantum computing?</i>
        </p>
    </div>
""", unsafe_allow_html=True)

# Helpers
def fetch_news(topic):
    """Fetch news for a specific topic"""
    params = {
        'q': topic,
        'language': 'en',
        'apikey': NEWS_API_KEY,
        'size': 3
    }
    response = requests.get(NEWS_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        articles = data.get("results", [])
        if articles:
            summary = "\n\n".join([f"🔹 {a.get('title', 'No title')} - {a.get('description', 'No description')}" for a in articles])
            return summary
        return "No news found on this topic."
    return f"Failed to fetch news. Error: {response.status_code}"

def fetch_latest_news():
    """Fetch latest news using the latest endpoint"""
    params = {
        'language': 'en',
        'apikey': NEWS_API_KEY,
        'size': 5
    }
    response = requests.get(LATEST_NEWS_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        articles = data.get("results", [])
        if articles:
            summary = "\n\n".join([f"🔹 {a.get('title', 'No title')} - {a.get('description', 'No description')}" for a in articles])
            return summary
        return "No latest news available."
    return f"Failed to fetch latest news. Error: {response.status_code}"

def fetch_latest_news_for_interests():
    """Fetch latest news for all user interests"""
    if not st.session_state.user_interests:
        return "Please select your interests first to get personalized news."
    
    all_news = []
    for topic in st.session_state.user_interests:
        params = {
            'q': topic,
            'language': 'en',
            'apikey': NEWS_API_KEY,
            'size': 2  # Reduced to fit all topics
        }
        response = requests.get(NEWS_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            articles = data.get("results", [])
            if articles:
                topic_news = f"\n📰 **{topic} News:**\n"
                topic_news += "\n".join([f"🔹 {a.get('title', 'No title')} - {a.get('description', 'No description')}" for a in articles[:2]])
                all_news.append(topic_news)
    
    if all_news:
        return "\n\n".join(all_news)
    return "No news found for your selected interests."

def fetch_general_latest_news():
    """Fetch general latest news when no specific topic is requested"""
    return fetch_latest_news()

def speak_text(text):
    tts = gTTS(text)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        st.session_state.is_playing_audio = True
        st.audio(fp.name, format="audio/mp3")
        st.session_state.is_playing_audio = False

def speak_text_with_interruption(text):
    """Speak text with ability to be interrupted by echo detection"""
    tts = gTTS(text)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        st.session_state.is_playing_audio = True
        st.session_state.current_news_text = text
        
        # Check for echo detection while playing
        audio_player = st.audio(fp.name, format="audio/mp3")
        
        # Monitor for echo detection
        if st.session_state.echo_detected:
            st.session_state.is_playing_audio = False
            return False  # Audio was interrupted
        
        st.session_state.is_playing_audio = False
        return True  # Audio completed normally

def detect_echo_in_text(text):
    """Enhanced echo detection with various trigger phrases"""
    text_lower = text.lower().strip()
    echo_triggers = [
        "echo",
        "hey echo",
        "echo news",
        "echo please",
        "stop and echo",
        "interrupt echo"
    ]
    
    for trigger in echo_triggers:
        if trigger in text_lower:
            return True, text_lower.replace(trigger, "").strip()
    
    return False, ""

def listen_to_user():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        # Show listening animation
        st.markdown("""
            <div class="status-listening">
                <div class="waveform">
                    <div class="waveform-bar"></div>
                    <div class="waveform-bar"></div>
                    <div class="waveform-bar"></div>
                    <div class="waveform-bar"></div>
                    <div class="waveform-bar"></div>
                    <div class="waveform-bar"></div>
                    <div class="waveform-bar"></div>
                </div>
                <p>🎙️ Listening... Please speak.</p>
            </div>
        """, unsafe_allow_html=True)
        
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            st.markdown(f"""
                <div class="status-success">
                    <p>✅ You said: <strong>{text}</strong></p>
                </div>
            """, unsafe_allow_html=True)
            return text
        except sr.UnknownValueError:
            st.markdown("""
                <div class="status-error">
                    <p>❌ Could not understand your speech.</p>
                </div>
            """, unsafe_allow_html=True)
        except sr.RequestError:
            st.markdown("""
                <div class="status-error">
                    <p>⚠️ Error with speech recognition service.</p>
                </div>
            """, unsafe_allow_html=True)
    return ""

def is_general_question(text):
    return bool(re.search(r"\b(what|who|when|where|why|how|explain|define)\b", text.lower())) or "?" in text

def is_latest_news_request(text):
    """Check if user is asking for latest news"""
    latest_keywords = ['latest', 'recent', 'current', 'today', 'news', 'update']
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in latest_keywords)

def create_chat_bubble(content, is_ai=False):
    if is_ai:
        return f"""
        <div class="chat-bubble" style="margin-left: 3rem;">
            <div style="display: flex; align-items: flex-start;">
                <div class="ai-avatar">🤖</div>
                <div style="flex: 1;">
                    {content}
                </div>
            </div>
        </div>
        """
    else:
        return f"""
        <div class="chat-bubble" style="margin-right: 3rem; background: rgba(102, 126, 234, 0.1);">
            <div style="display: flex; align-items: flex-start;">
                <div style="flex: 1; text-align: right;">
                    {content}
                </div>
                <div class="ai-avatar" style="margin-left: 1rem; margin-right: 0;">👤</div>
            </div>
        </div>
        """

def render_topic_selection():
    """Render the topic selection interface"""
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown('<p class="section-header">🎯 Choose Your Interests (Up to 5)</p>', unsafe_allow_html=True)
    st.markdown('<p style="color: rgba(255, 255, 255, 0.8); text-align: center; margin-bottom: 2rem;">Select the topics you\'re most interested in to get personalized news.</p>', unsafe_allow_html=True)
    
    # Initialize session state for topic selections
    if 'topic_selections' not in st.session_state:
        st.session_state.topic_selections = {}
    
    # Create topic selection grid
    cols = st.columns(2)
    for i, (topic, info) in enumerate(AVAILABLE_TOPICS.items()):
        col = cols[i % 2]
        with col:
            # Initialize topic selection state
            if topic not in st.session_state.topic_selections:
                st.session_state.topic_selections[topic] = topic in st.session_state.user_interests
            
            is_selected = st.session_state.topic_selections[topic]
            selected_class = "selected" if is_selected else ""
            
            st.markdown(f"""
                <div class="topic-card {selected_class}">
                    <div class="topic-icon">{info['icon']}</div>
                    <div class="topic-name">{topic}</div>
                    <div class="topic-description">{info['description']}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Handle checkbox state
            checkbox_key = f"checkbox_{topic}"
            if st.checkbox(f"Select {topic}", key=checkbox_key, value=is_selected):
                if topic not in st.session_state.user_interests and len(st.session_state.user_interests) < 5:
                    st.session_state.user_interests.append(topic)
                    st.session_state.topic_selections[topic] = True
            else:
                if topic in st.session_state.user_interests:
                    st.session_state.user_interests.remove(topic)
                    st.session_state.topic_selections[topic] = False
    
    # Show selected interests
    if st.session_state.user_interests:
        st.markdown(f"""
            <div style="background: rgba(102, 126, 234, 0.1); border-radius: 12px; padding: 1rem; margin: 1rem 0;">
                <p style="color: #667eea; font-weight: 600; margin-bottom: 0.5rem;">Selected Interests ({len(st.session_state.user_interests)}/5):</p>
                <p style="color: rgba(255, 255, 255, 0.8);">{', '.join(st.session_state.user_interests)}</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Save interests button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("💾 Save Interests", key="save_interests", use_container_width=True):
            if st.session_state.user_interests:
                st.session_state.interests_set = True
                st.success("✅ Interests saved! You can now ask for latest news or specific topics.")
                time.sleep(1)
                st.rerun()
            else:
                st.error("Please select at least one interest.")
    
    st.markdown('</div>', unsafe_allow_html=True)

def continuous_listen():
    """Background thread for continuous listening"""
    try:
        recognizer = sr.Recognizer()
        
        # Test microphone access first
        try:
            with sr.Microphone() as source:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=1)
                st.session_state.microphone_available = True
        except Exception as e:
            print(f"Microphone initialization error: {e}")
            st.session_state.microphone_available = False
            st.session_state.microphone_error = str(e)
            return
        
        # Main listening loop
        with sr.Microphone() as source:
            while st.session_state.continuous_listening:
                try:
                    # Listen for audio with longer timeout for continuous listening
                    audio = recognizer.listen(source, timeout=300, phrase_time_limit=300)
                    text = recognizer.recognize_google(audio)
                    
                    if text:
                        print(f"Continuous listening heard: {text}")
                        # Enhanced echo detection
                        is_echo, query = detect_echo_in_text(text)
                        
                        if is_echo:
                            st.session_state.echo_detected = True
                            st.session_state.paused_news_text = st.session_state.current_news_text
                            st.session_state.is_playing_audio = False
                            
                            # Set the new query
                            if query:
                                st.session_state.new_query = query
                            else:
                                st.session_state.new_query = "general news"
                            
                            # Put the detection in queue for main thread to process
                            st.session_state.audio_queue.put(("echo_detected", text))
                        else:
                            # Regular speech detected
                            st.session_state.audio_queue.put(("speech", text))
                            
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    continue
                except Exception as e:
                    print(f"Error in continuous listening: {e}")
                    continue
                    
    except Exception as e:
        print(f"Critical error in continuous listening: {e}")
        st.session_state.continuous_listening = False
        st.session_state.microphone_error = str(e)

def start_continuous_listening():
    """Start continuous listening in background thread"""
    if not st.session_state.continuous_listening:
        try:
            # Reset microphone status
            st.session_state.microphone_available = True
            st.session_state.microphone_error = None
            
            st.session_state.continuous_listening = True
            st.session_state.listening_start_time = time.time()
            st.session_state.listening_thread = threading.Thread(target=continuous_listen, daemon=True)
            st.session_state.listening_thread.start()
            
            # Give the thread a moment to initialize
            time.sleep(0.5)
            
            # Check if microphone initialization was successful
            if not st.session_state.microphone_available:
                st.session_state.continuous_listening = False
                st.error(f"❌ Microphone not available: {st.session_state.microphone_error}")
                return False
                
            return True
            
        except Exception as e:
            st.session_state.continuous_listening = False
            st.error(f"❌ Failed to start continuous listening: {str(e)}")
            return False
    return True

def stop_continuous_listening():
    """Stop continuous listening"""
    if st.session_state.continuous_listening:
        st.session_state.continuous_listening = False
        if st.session_state.listening_start_time:
            st.session_state.total_listening_time += time.time() - st.session_state.listening_start_time
            st.session_state.listening_start_time = None
        if st.session_state.listening_thread:
            st.session_state.listening_thread.join(timeout=3)

def process_echo_detection():
    """Process echo detection and handle new query"""
    if st.session_state.echo_detected:
        st.session_state.echo_detected = False
        st.session_state.echo_count += 1
        
        # Show echo detection message
        st.markdown("""
            <div class="status-echo">
                <p>🔄 Echo detected! Pausing current news...</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Handle the new query
        query = st.session_state.new_query
        st.markdown(create_chat_bubble(f"<strong>New Query: {query}</strong>", is_ai=False), unsafe_allow_html=True)
        
        if is_latest_news_request(query):
            st.markdown('<p class="section-header">📰 Latest News for Your Interests:</p>', unsafe_allow_html=True)
            latest_news = fetch_latest_news_for_interests()
            st.markdown(create_chat_bubble(latest_news, is_ai=True), unsafe_allow_html=True)
            speak_text(latest_news)
        
        elif is_general_question(query):
            st.markdown('<p class="section-header">🤖 Gemini Answer:</p>', unsafe_allow_html=True)
            answer = ask_gemini(query)
            st.markdown(create_chat_bubble(answer, is_ai=True), unsafe_allow_html=True)
            speak_text(answer)
        
        elif query.lower() in ['general news', 'latest', 'recent', 'current', 'today']:
            st.markdown('<p class="section-header">📰 Latest News:</p>', unsafe_allow_html=True)
            latest_news = fetch_general_latest_news()
            st.markdown(create_chat_bubble(latest_news, is_ai=True), unsafe_allow_html=True)
            speak_text(latest_news)
        
        else:
            summary = fetch_news(query)
            st.markdown('<p class="section-header">📰 News Summary:</p>', unsafe_allow_html=True)
            st.markdown(create_chat_bubble(summary, is_ai=True), unsafe_allow_html=True)
            speak_text(summary)
        
        # Resume previous news
        if st.session_state.paused_news_text:
            st.markdown('<p class="section-header">🔁 Resuming Previous News:</p>', unsafe_allow_html=True)
            st.markdown(create_chat_bubble(st.session_state.paused_news_text, is_ai=True), unsafe_allow_html=True)
            speak_text(st.session_state.paused_news_text)
            st.session_state.paused_news_text = ""

def check_audio_queue():
    """Check for new audio input from background thread"""
    try:
        while not st.session_state.audio_queue.empty():
            event_type, text = st.session_state.audio_queue.get_nowait()
            
            if event_type == "echo_detected":
                process_echo_detection()
            elif event_type == "speech":
                # Handle regular speech input
                st.markdown(create_chat_bubble(f"<strong>Heard: {text}</strong>", is_ai=False), unsafe_allow_html=True)
                
    except queue.Empty:
        pass

def cleanup_on_exit():
    """Cleanup function to stop continuous listening on app exit"""
    if st.session_state.continuous_listening:
        stop_continuous_listening()

# Register cleanup
import atexit
atexit.register(cleanup_on_exit)

def test_microphone():
    """Test microphone functionality"""
    try:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("🎤 Testing microphone... Please speak something.")
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=30)
            text = recognizer.recognize_google(audio)
            st.success(f"✅ Microphone test successful! Heard: '{text}'")
            return True
    except sr.WaitTimeoutError:
        st.error("❌ No speech detected during test. Please try again.")
        return False
    except sr.UnknownValueError:
        st.error("❌ Could not understand speech during test. Please try again.")
        return False
    except Exception as e:
        st.error(f"❌ Microphone test failed: {str(e)}")
        return False

# Main UI
if not st.session_state.interests_set:
    render_topic_selection()
else:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    # Show current interests
    st.markdown(f"""
        <div style="background: rgba(102, 126, 234, 0.1); border-radius: 12px; padding: 1rem; margin-bottom: 2rem;">
            <p style="color: #667eea; font-weight: 600; margin-bottom: 0.5rem;">Your Interests:</p>
            <p style="color: rgba(255, 255, 255, 0.8);">{', '.join(st.session_state.user_interests)}</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Continuous listening controls
    st.markdown('<p class="section-header">🎙️ Continuous Listening</p>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        if st.button("🎤 Start Continuous Listening", key="start_listening", use_container_width=True):
            success = start_continuous_listening()
            if success:
                st.success("✅ Continuous listening started! Say 'echo' followed by your query to interrupt news.")
            else:
                st.error("❌ Failed to start continuous listening. Please check your microphone permissions.")
    
    with col2:
        if st.button("⏹️ Stop Listening", key="stop_listening", use_container_width=True):
            stop_continuous_listening()
            st.success("✅ Continuous listening stopped.")
    
    with col3:
        if st.button("🔍 Test Microphone", key="test_mic", use_container_width=True):
            test_microphone()
    
    with col4:
        if st.button("🔄 Change Interests", key="change_interests"):
            stop_continuous_listening()
            st.session_state.interests_set = False
            st.rerun()
    
    # Show microphone status
    if st.session_state.microphone_error:
        st.markdown(f"""
            <div class="status-error">
                <p>❌ Microphone Error: {st.session_state.microphone_error}</p>
                <p style="font-size: 0.9rem;">Please check your microphone permissions and try again.</p>
            </div>
        """, unsafe_allow_html=True)
    
    # Show listening status
    if st.session_state.continuous_listening:
        # Calculate current listening time
        current_time = time.time()
        listening_duration = current_time - st.session_state.listening_start_time if st.session_state.listening_start_time else 0
        total_time = st.session_state.total_listening_time + listening_duration
        
        st.markdown(f"""
            <div class="status-continuous">
                <div class="waveform">
                    <div class="waveform-bar"></div>
                    <div class="waveform-bar"></div>
                    <div class="waveform-bar"></div>
                    <div class="waveform-bar"></div>
                    <div class="waveform-bar"></div>
                    <div class="waveform-bar"></div>
                    <div class="waveform-bar"></div>
                </div>
                <p>🎙️ Continuously listening... Say "echo" + your query to interrupt news</p>
                <p style="font-size: 0.9rem; margin-top: 0.5rem; opacity: 0.8;">
                    ⏱️ Listening for: {int(listening_duration)}s | 
                    🔄 Echo detections: {st.session_state.echo_count} | 
                    ⏱️ Total time: {int(total_time)}s
                </p>
            </div>
        """, unsafe_allow_html=True)
    
    # Check for audio input from background thread
    check_audio_queue()
    
    # Manual voice input (for testing)
    st.markdown('<p class="section-header">🎤 Manual Voice Input</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
            <div style="text-align: center; margin: 2rem 0;">
                <p style="color: rgba(255, 255, 255, 0.8); margin-bottom: 1rem; font-size: 1.1rem;">
                    Or tap the button below for manual voice input
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🎤 Tap to Speak", key="main_button"):
            user_input = listen_to_user()

            if user_input:
                # Show user input in chat bubble
                st.markdown(create_chat_bubble(f"<strong>{user_input}</strong>", is_ai=False), unsafe_allow_html=True)
                
                # Store current news text for potential pause/resume
                if is_latest_news_request(user_input):
                    st.markdown('<p class="section-header">📰 Latest News for Your Interests:</p>', unsafe_allow_html=True)
                    latest_news = fetch_latest_news_for_interests()
                    st.session_state.current_news_text = latest_news
                    st.markdown(create_chat_bubble(latest_news, is_ai=True), unsafe_allow_html=True)
                    speak_text(latest_news)
                
                elif is_general_question(user_input):
                    st.markdown('<p class="section-header">🤖 Gemini Answer:</p>', unsafe_allow_html=True)
                    answer = ask_gemini(user_input)
                    st.markdown(create_chat_bubble(answer, is_ai=True), unsafe_allow_html=True)
                    speak_text(answer)

                    if 'last_topic' in st.session_state:
                        st.markdown('<p class="section-header">🔁 Resuming News:</p>', unsafe_allow_html=True)
                        summary = fetch_news(st.session_state['last_topic'])
                        st.session_state.current_news_text = summary
                        st.markdown(create_chat_bubble(summary, is_ai=True), unsafe_allow_html=True)
                        speak_text(summary)

                elif user_input.lower() in ['general news', 'latest', 'recent', 'current', 'today']:
                    st.markdown('<p class="section-header">📰 Latest News:</p>', unsafe_allow_html=True)
                    latest_news = fetch_general_latest_news()
                    st.session_state.current_news_text = latest_news
                    st.markdown(create_chat_bubble(latest_news, is_ai=True), unsafe_allow_html=True)
                    speak_text(latest_news)

                else:
                    st.session_state['last_topic'] = user_input
                    summary = fetch_news(user_input)
                    st.session_state.current_news_text = summary
                    st.markdown('<p class="section-header">📰 News Summary:</p>', unsafe_allow_html=True)
                    st.markdown(create_chat_bubble(summary, is_ai=True), unsafe_allow_html=True)
                    speak_text(summary)
    
    # Instructions
    st.markdown("""
        <div class="instructions-box">
            <h4>📋 How to Use Echo Feature:</h4>
            <ul>
                <li><strong>🔍 Test Microphone:</strong> Click "Test Microphone" first to verify your mic is working</li>
                <li><strong>🎙️ Start Continuous Listening:</strong> Click the button to enable background listening</li>
                <li><strong>📰 Listen to News:</strong> Ask for news topics and listen to the audio</li>
                <li><strong>🔄 Interrupt with "Echo":</strong> Say "echo" followed by your new query to pause current news</li>
                <li><strong>📝 Examples:</strong> "echo what is quantum computing", "echo latest technology news"</li>
                <li><strong>🔁 Auto-Resume:</strong> After handling your new query, the previous news will automatically resume</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)
    
    # Troubleshooting section
    st.markdown("""
        <div style="background: rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 1.5rem; margin: 2rem 0;">
            <h4 style="color: #f59e0b; margin-bottom: 1rem;">🔧 Troubleshooting:</h4>
            <ul style="color: rgba(255, 255, 255, 0.8); line-height: 1.6; margin: 0; padding-left: 1.5rem;">
                <li><strong>Microphone not working?</strong> Click "Test Microphone" to verify permissions</li>
                <li><strong>Browser blocking microphone?</strong> Allow microphone access when prompted</li>
                <li><strong>No speech detected?</strong> Try speaking louder or check your microphone settings</li>
                <li><strong>Continuous listening not starting?</strong> Check browser console for errors</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
                
