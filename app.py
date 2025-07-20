import streamlit as st
import streamlit.components.v1 as components
import os
import json
from datetime import datetime, timedelta
import logging

# Import backend components
try:
    from backend.audio_manager import AudioManager
    from backend.rag_engine import RAGEngine
    from backend.news_fetcher import NewsFetcher
    from backend.summarizer import NewsSummarizer
    from backend.fact_checker import FactChecker
    from components.news_player import NewsPlayer
except ImportError as e:
    st.error(f"Error importing backend components: {e}")
    st.info("Please ensure all backend components are properly installed.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('echonews.log')
    ]
)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="EchoNews - AI-Powered News Assistant",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'current_news' not in st.session_state:
    st.session_state.current_news = None
if 'audio_playing' not in st.session_state:
    st.session_state.audio_playing = False
if 'user_question' not in st.session_state:
    st.session_state.user_question = ""
if 'aspirant_mode' not in st.session_state:
    st.session_state.aspirant_mode = False
if 'bookmarks' not in st.session_state:
    st.session_state.bookmarks = []
if 'current_language' not in st.session_state:
    st.session_state.current_language = "en"

# Initialize backend components
@st.cache_resource
def get_audio_manager():
    try:
        return AudioManager()
    except Exception as e:
        st.error(f"Error initializing AudioManager: {e}")
        return None

@st.cache_resource
def get_rag_engine():
    try:
        return RAGEngine()
    except Exception as e:
        st.error(f"Error initializing RAGEngine: {e}")
        return None

@st.cache_resource
def get_news_fetcher():
    try:
        return NewsFetcher()
    except Exception as e:
        st.error(f"Error initializing NewsFetcher: {e}")
        return None

@st.cache_resource
def get_summarizer():
    try:
        return NewsSummarizer()
    except Exception as e:
        st.error(f"Error initializing NewsSummarizer: {e}")
        return None

@st.cache_resource
def get_fact_checker():
    try:
        return FactChecker()
    except Exception as e:
        st.error(f"Error initializing FactChecker: {e}")
        return None

@st.cache_resource
def get_news_player():
    try:
        return NewsPlayer()
    except Exception as e:
        st.error(f"Error initializing NewsPlayer: {e}")
        return None

# Load CSS
def load_css():
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
    }
    
    .news-card {
        background: linear-gradient(145deg, #ffffff 0%, #fafbfc 100%);
        padding: 1.8rem;
        border-radius: 12px;
        border-left: 5px solid #007bff;
        margin: 1.5rem 0;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .news-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.15);
    }
    
    .aspirant-mode {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .quiz-card {
        background: linear-gradient(145deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #28a745;
    }
    
    .status-box {
        padding: 1rem 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        font-weight: 600;
        font-size: 1rem;
        border-left: 4px solid #007bff;
        background: #f8f9fa;
        color: #495057;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .status-success {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        color: #155724;
        border-left-color: #28a745;
    }
    
    .status-warning {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        color: #856404;
        border-left-color: #ffc107;
    }
    
    .status-error {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        color: #721c24;
        border-left-color: #dc3545;
    }
    
    .language-selector {
        background: linear-gradient(145deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

load_css()

# Main header
st.markdown("""
<div class="main-header">
    <h1>📰 EchoNews - AI-Powered News Assistant</h1>
    <p>Listen to news, ask questions, and get intelligent responses</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🎛️ Settings")
    
    # Language selection
    st.markdown("#### 🌐 Language")
    language = st.selectbox(
        "Select Language",
        ["English", "Malayalam"],
        index=0 if st.session_state.current_language == "en" else 1
    )
    st.session_state.current_language = "en" if language == "English" else "ml"
    
    # Aspirant Mode toggle
    st.markdown("#### 🎯 Aspirant Mode")
    aspirant_mode = st.checkbox(
        "Enable UPSC/PSC Mode",
        value=st.session_state.aspirant_mode,
        help="Get curated current affairs for competitive exams"
    )
    st.session_state.aspirant_mode = aspirant_mode
    
    if aspirant_mode:
        st.markdown("""
        <div class="aspirant-mode">
            <h4>🎯 UPSC/PSC Features:</h4>
            <ul>
                <li>Daily current affairs</li>
                <li>MCQ quizzes</li>
                <li>Bookmarks</li>
                <li>Date-wise news</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Bookmarks
    if st.session_state.bookmarks:
        st.markdown("#### 🔖 Bookmarks")
        for i, bookmark in enumerate(st.session_state.bookmarks):
            if st.button(f"📌 {bookmark['title'][:30]}...", key=f"bookmark_{i}"):
                st.session_state.current_news = bookmark
                st.rerun()

# Main content
tab1, tab2, tab3, tab4 = st.tabs(["📰 News", "🎧 Audio Player", "❓ Q&A", "📊 Aspirant Mode"])

with tab1:
    st.markdown("### 📰 Latest News")
    
    # Fetch news
    news_fetcher = get_news_fetcher()
    if news_fetcher:
        news_list = news_fetcher.get_latest_news()
        
        if news_list:
            for i, news in enumerate(news_list):
                with st.container():
                    st.markdown(f"""
                    <div class="news-card">
                        <h4>{i+1}. {news['title']}</h4>
                        <p><strong>Source:</strong> {news['source']} | <strong>Date:</strong> {news['date']}</p>
                        <p>{news['summary']}</p>
                        <p><strong>Credibility Score:</strong> {news['credibility_score']}/10</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        if st.button("🎧 Listen", key=f"listen_{i}"):
                            st.session_state.current_news = news
                            st.session_state.audio_playing = True
                            st.rerun()
                    
                    with col2:
                        if st.button("📌 Bookmark", key=f"bookmark_{i}"):
                            if news not in st.session_state.bookmarks:
                                st.session_state.bookmarks.append(news)
                                st.success("News bookmarked!")
                    
                    with col3:
                        if st.button("📝 Summary", key=f"summary_{i}"):
                            summarizer = get_summarizer()
                            if summarizer:
                                summary = summarizer.generate_summary(news['content'])
                                st.info(f"Summary: {summary}")
                    
                    with col4:
                        if st.button("❓ Quiz", key=f"quiz_{i}"):
                            st.session_state.current_news = news
                            st.rerun()
        else:
            st.warning("No news available at the moment.")
    else:
        st.error("News fetcher not available. Please check the backend components.")

with tab2:
    st.markdown("### 🎧 Audio Player")
    
    if st.session_state.current_news:
        news_player = get_news_player()
        if news_player:
            audio_html = news_player.create_audio_player(
                st.session_state.current_news,
                st.session_state.current_language
            )
            
            st.markdown(audio_html, unsafe_allow_html=True)
            
            # Voice input for questions
            st.markdown("### 🎤 Ask Questions")
            st.markdown("Speak your question while news is playing:")
            
            # Voice interaction component
            voice_html = news_player.create_voice_interaction_ui()
            st.markdown(voice_html, unsafe_allow_html=True)
            
            # Question input
            user_question = st.text_input("Or type your question:", key="question_input")
            
            if user_question:
                st.session_state.user_question = user_question
                
                # Process question with RAG
                rag_engine = get_rag_engine()
                if rag_engine:
                    answer = rag_engine.answer_question(user_question, st.session_state.current_news)
                    
                    st.markdown("### 💡 Answer")
                    st.markdown(f"""
                    <div class="news-card">
                        <h4>Question: {user_question}</h4>
                        <p><strong>Answer:</strong> {answer}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.error("RAG engine not available.")
        else:
            st.error("News player not available.")
    else:
        st.info("Please select a news article from the News tab to start listening.")

with tab3:
    st.markdown("### ❓ Question & Answer")
    
    st.markdown("Ask questions about current affairs, politics, economics, or any topic:")
    
    question = st.text_area("Enter your question:", height=100)
    
    if st.button("🔍 Get Answer", type="primary"):
        if question:
            rag_engine = get_rag_engine()
            if rag_engine:
                answer = rag_engine.answer_general_question(question)
                
                st.markdown("### 💡 Answer")
                st.markdown(f"""
                <div class="news-card">
                    <h4>Question: {question}</h4>
                    <p><strong>Answer:</strong> {answer}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.error("RAG engine not available.")
        else:
            st.warning("Please enter a question.")

with tab4:
    if st.session_state.aspirant_mode:
        st.markdown("### 🎯 Aspirant Mode - UPSC/PSC Preparation")
        
        # Daily current affairs
        st.markdown("#### 📅 Daily Current Affairs")
        
        # Date selector
        selected_date = st.date_input(
            "Select Date:",
            value=datetime.now().date(),
            max_value=datetime.now().date()
        )
        
        # Get news for selected date
        news_fetcher = get_news_fetcher()
        if news_fetcher:
            daily_news = news_fetcher.get_daily_news(selected_date)
            
            if daily_news:
                for i, news in enumerate(daily_news):
                    with st.container():
                        st.markdown(f"""
                        <div class="news-card">
                            <h4>{i+1}. {news['title']}</h4>
                            <p><strong>Category:</strong> {news['category']} | <strong>Date:</strong> {news['date']}</p>
                            <p>{news['summary']}</p>
                            <p><strong>Relevance to UPSC:</strong> {news['upsc_relevance']}</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("📝 Generate MCQs", key=f"mcq_{i}"):
                                summarizer = get_summarizer()
                                if summarizer:
                                    mcqs = summarizer.generate_mcq_from_news(news)
                                    if mcqs:
                                        st.markdown("### 🧠 Generated MCQs")
                                        for j, mcq in enumerate(mcqs):
                                            st.markdown(f"""
                                            <div class="quiz-card">
                                                <h5>Q{j+1}: {mcq['question']}</h5>
                                                <ul>
                                                    <li>A) {mcq['options'][0]}</li>
                                                    <li>B) {mcq['options'][1]}</li>
                                                    <li>C) {mcq['options'][2]}</li>
                                                    <li>D) {mcq['options'][3]}</li>
                                                </ul>
                                                <p><strong>Answer:</strong> {chr(65 + mcq['correct_answer'])}</p>
                                                <p><em>{mcq['explanation']}</em></p>
                                            </div>
                                            """, unsafe_allow_html=True)
                        
                        with col2:
                            if st.button("📌 Bookmark", key=f"aspirant_bookmark_{i}"):
                                if news not in st.session_state.bookmarks:
                                    st.session_state.bookmarks.append(news)
                                    st.success("News bookmarked!")
            else:
                st.info("No news available for the selected date.")
        else:
            st.error("News fetcher not available.")
        
        # Smart Quiz section
        st.markdown("#### 🧠 Smart Quiz")
        
        if st.button("🎯 Generate Quiz", type="primary"):
            st.info("Quiz generation feature coming soon!")
            
            # Mock quiz
            st.markdown("""
            <div class="quiz-card">
                <h4>Sample MCQ:</h4>
                <p><strong>Q:</strong> What is the current repo rate set by RBI?</p>
                <ul>
                    <li>A) 6.25%</li>
                    <li>B) 6.50%</li>
                    <li>C) 6.75%</li>
                    <li>D) 7.00%</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        # Daily Summary Podcast
        st.markdown("#### 🎧 Daily Summary Podcast")
        
        if st.button("🎙️ Generate Daily Podcast", type="primary"):
            st.info("Daily podcast generation feature coming soon!")
            
            # Mock podcast
            st.markdown("""
            <div class="news-card">
                <h4>📻 Daily News Summary (5 min)</h4>
                <p>Top headlines and current affairs for competitive exam preparation.</p>
                <audio controls style="width: 100%; margin: 10px 0;">
                    <source src="data:audio/mp3;base64," type="audio/mp3">
                    Your browser does not support the audio element.
                </audio>
            </div>
            """, unsafe_allow_html=True)
    
    else:
        st.markdown("### 🎯 Enable Aspirant Mode")
        st.info("Please enable Aspirant Mode in the sidebar to access UPSC/PSC features.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6c757d; padding: 1rem;">
    <p>📰 EchoNews - AI-Powered News Assistant | Built with ❤️ using Streamlit</p>
</div>
""", unsafe_allow_html=True) 