#!/usr/bin/env python3
"""
Test script for EchoNews application
Run this script to verify all components work correctly
"""

import sys
import os
import logging
from datetime import datetime

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test if all required modules can be imported"""
    logger.info("Testing imports...")
    
    try:
        from backend.audio_manager import AudioManager
        logger.info("✅ AudioManager imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import AudioManager: {e}")
        return False
    
    try:
        from backend.rag_engine import RAGEngine
        logger.info("✅ RAGEngine imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import RAGEngine: {e}")
        return False
    
    try:
        from backend.news_fetcher import NewsFetcher
        logger.info("✅ NewsFetcher imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import NewsFetcher: {e}")
        return False
    
    try:
        from backend.summarizer import NewsSummarizer
        logger.info("✅ NewsSummarizer imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import NewsSummarizer: {e}")
        return False
    
    try:
        from backend.fact_checker import FactChecker
        logger.info("✅ FactChecker imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import FactChecker: {e}")
        return False
    
    try:
        from components.news_player import NewsPlayer
        logger.info("✅ NewsPlayer imported successfully")
    except ImportError as e:
        logger.error(f"❌ Failed to import NewsPlayer: {e}")
        return False
    
    return True

def test_news_fetcher():
    """Test news fetcher functionality"""
    logger.info("Testing news fetcher...")
    
    try:
        from backend.news_fetcher import NewsFetcher
        news_fetcher = NewsFetcher()
        
        # Test getting latest news
        news_list = news_fetcher.get_latest_news()
        assert len(news_list) > 0, "No news returned"
        logger.info(f"✅ News fetcher returned {len(news_list)} articles")
        
        # Test getting news by category
        economics_news = news_fetcher.get_news_by_category("Economics")
        assert len(economics_news) > 0, "No economics news found"
        logger.info(f"✅ Found {len(economics_news)} economics articles")
        
        # Test search functionality
        search_results = news_fetcher.search_news("RBI")
        assert len(search_results) > 0, "No search results for 'RBI'"
        logger.info(f"✅ Search returned {len(search_results)} results")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ News fetcher test failed: {e}")
        return False

def test_rag_engine():
    """Test RAG engine functionality"""
    logger.info("Testing RAG engine...")
    
    try:
        from backend.rag_engine import RAGEngine
        rag_engine = RAGEngine()
        
        # Test answering a question
        question = "What is the current repo rate?"
        answer = rag_engine.answer_question(question)
        assert len(answer) > 0, "No answer generated"
        logger.info(f"✅ RAG engine answered: {answer[:100]}...")
        
        # Test general question answering
        general_answer = rag_engine.answer_general_question("What is GDP?")
        assert len(general_answer) > 0, "No general answer generated"
        logger.info(f"✅ General Q&A working: {general_answer[:100]}...")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ RAG engine test failed: {e}")
        return False

def test_summarizer():
    """Test news summarizer functionality"""
    logger.info("Testing news summarizer...")
    
    try:
        from backend.summarizer import NewsSummarizer
        summarizer = NewsSummarizer()
        
        # Test content
        test_content = """
        The Reserve Bank of India (RBI) has decided to maintain the repo rate at 6.50% for the fourth consecutive time. 
        This decision comes amid concerns about inflation and global economic uncertainties. 
        The Monetary Policy Committee (MPC) voted 5-1 in favor of keeping the rate unchanged. 
        RBI Governor Shaktikanta Das stated that the central bank remains focused on bringing inflation down to the target of 4% while supporting economic growth.
        """
        
        # Test concise summary
        concise_summary = summarizer.generate_summary(test_content, "concise")
        assert len(concise_summary) > 0, "No concise summary generated"
        logger.info(f"✅ Concise summary: {concise_summary[:100]}...")
        
        # Test detailed summary
        detailed_summary = summarizer.generate_summary(test_content, "detailed")
        assert len(detailed_summary) > 0, "No detailed summary generated"
        logger.info(f"✅ Detailed summary: {detailed_summary[:100]}...")
        
        # Test bullet summary
        bullet_summary = summarizer.generate_summary(test_content, "bullet")
        assert len(bullet_summary) > 0, "No bullet summary generated"
        logger.info(f"✅ Bullet summary generated with {bullet_summary.count('•')} points")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Summarizer test failed: {e}")
        return False

def test_fact_checker():
    """Test fact checker functionality"""
    logger.info("Testing fact checker...")
    
    try:
        from backend.fact_checker import FactChecker
        fact_checker = FactChecker()
        
        # Test news data
        test_news = {
            "title": "RBI Maintains Repo Rate at 6.50%",
            "content": "The Reserve Bank of India has decided to maintain the repo rate at 6.50% for the fourth consecutive time.",
            "source": "RBI Official",
            "date": "2024-02-08"
        }
        
        # Test credibility check
        credibility_result = fact_checker.check_credibility(test_news)
        assert "overall_score" in credibility_result, "No credibility score returned"
        logger.info(f"✅ Credibility score: {credibility_result['overall_score']}")
        
        # Test batch checking
        news_list = [test_news]
        batch_results = fact_checker.batch_check_credibility(news_list)
        assert len(batch_results) > 0, "No batch results returned"
        logger.info(f"✅ Batch credibility check completed for {len(batch_results)} articles")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fact checker test failed: {e}")
        return False

def test_audio_manager():
    """Test audio manager functionality"""
    logger.info("Testing audio manager...")
    
    try:
        from backend.audio_manager import AudioManager
        audio_manager = AudioManager()
        
        # Test getting audio files
        audio_files = audio_manager.get_audio_files()
        logger.info(f"✅ Found {len(audio_files)} audio files")
        
        # Test audio file management
        test_filename = "test_audio.mp3"
        delete_result = audio_manager.delete_audio_file(test_filename)
        logger.info(f"✅ Audio file management working")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Audio manager test failed: {e}")
        return False

def test_news_player():
    """Test news player functionality"""
    logger.info("Testing news player...")
    
    try:
        from components.news_player import NewsPlayer
        news_player = NewsPlayer()
        
        # Test news data
        test_news = {
            "title": "Test News Article",
            "summary": "This is a test news article for testing purposes.",
            "source": "Test Source",
            "date": "2024-02-08",
            "id": "test_1"
        }
        
        # Test audio player creation
        audio_html = news_player.create_audio_player(test_news, "en")
        assert len(audio_html) > 0, "No audio HTML generated"
        logger.info("✅ Audio player HTML generated successfully")
        
        # Test voice interaction UI
        voice_html = news_player.create_voice_interaction_ui()
        assert len(voice_html) > 0, "No voice interaction HTML generated"
        logger.info("✅ Voice interaction UI generated successfully")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ News player test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🚀 Starting EchoNews application tests...")
    
    tests = [
        ("Import Test", test_imports),
        ("News Fetcher Test", test_news_fetcher),
        ("RAG Engine Test", test_rag_engine),
        ("Summarizer Test", test_summarizer),
        ("Fact Checker Test", test_fact_checker),
        ("Audio Manager Test", test_audio_manager),
        ("News Player Test", test_news_player)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running {test_name}...")
        logger.info(f"{'='*50}")
        
        try:
            if test_func():
                logger.info(f"✅ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")
    
    logger.info(f"\n{'='*50}")
    logger.info(f"TEST RESULTS: {passed}/{total} tests passed")
    logger.info(f"{'='*50}")
    
    if passed == total:
        logger.info("🎉 All tests passed! EchoNews is ready to run.")
        logger.info("Run 'streamlit run app.py' to start the application.")
    else:
        logger.error(f"❌ {total - passed} tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 