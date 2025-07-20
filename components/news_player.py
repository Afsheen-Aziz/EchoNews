import streamlit as st
import streamlit.components.v1 as components
import logging
from typing import Dict, Optional
import base64
import os

logger = logging.getLogger(__name__)

class NewsPlayer:
    def __init__(self):
        self.audio_dir = "data/news"
        logger.info("NewsPlayer initialized")
    
    def create_audio_player(self, news_data: Dict, language: str = "en") -> str:
        """
        Create an HTML audio player for news
        
        Args:
            news_data (Dict): News article data
            language (str): Language code (en, ml)
            
        Returns:
            str: HTML audio player
        """
        try:
            title = news_data.get("title", "News Article")
            summary = news_data.get("summary", "")
            source = news_data.get("source", "Unknown")
            date = news_data.get("date", "")
            
            # Create voice-friendly text
            voice_text = f"Here's the latest news. {title}. {summary}. This news comes from {source}."
            
            # Generate audio file path (mock for now)
            audio_filename = f"news_{news_data.get('id', '1')}_{language}.mp3"
            audio_path = os.path.join(self.audio_dir, audio_filename)
            
            # Create HTML player
            html_content = f"""
            <div style="margin: 20px 0; padding: 20px; background: linear-gradient(145deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 15px; border-left: 5px solid #007bff;">
                <h4 style="color: #2c3e50; margin-bottom: 15px;">🎧 Audio News Player</h4>
                
                <div style="margin-bottom: 15px;">
                    <h5 style="color: #495057; margin-bottom: 10px;">{title}</h5>
                    <p style="color: #6c757d; font-size: 14px; margin-bottom: 5px;">
                        <strong>Source:</strong> {source} | <strong>Date:</strong> {date}
                    </p>
                    <p style="color: #495057; line-height: 1.6;">{summary}</p>
                </div>
                
                <div style="margin: 20px 0;">
                    <audio controls style="width: 100%; height: 40px;">
                        <source src="data:audio/mp3;base64," type="audio/mp3">
                        Your browser does not support the audio element.
                    </audio>
                </div>
                
                <div style="margin-top: 15px; padding: 10px; background: #e8f4fd; border-radius: 8px;">
                    <p style="color: #0c5460; font-size: 14px; margin: 0;">
                        🔊 <strong>Voice Interaction:</strong> Click the microphone button below to ask questions while listening
                    </p>
                </div>
            </div>
            """
            
            logger.info(f"Created audio player for news: '{title[:30]}...'")
            return html_content
            
        except Exception as e:
            logger.error(f"Error creating audio player: {str(e)}")
            return f"""
            <div style="color: red; padding: 10px; border: 1px solid red; border-radius: 5px;">
                ❌ Error creating audio player: {str(e)}
            </div>
            """
    
    def create_voice_interaction_ui(self) -> str:
        """
        Create voice interaction UI component
        
        Returns:
            str: HTML for voice interaction
        """
        try:
            html_content = """
            <div style="margin: 20px 0; padding: 20px; background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%); border-radius: 15px; border: 2px solid #e9ecef;">
                <h4 style="color: #2c3e50; margin-bottom: 15px;">🎤 Voice Interaction</h4>
                
                <div style="text-align: center; margin-bottom: 20px;">
                    <button id="voiceBtn" style="
                        padding: 15px 30px; 
                        font-size: 16px; 
                        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
                        color: white; 
                        border: none; 
                        border-radius: 25px; 
                        cursor: pointer;
                        margin: 10px;
                        font-weight: 600;
                        box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
                        transition: all 0.3s ease;
                    ">🎤 Ask Question</button>
                    
                    <div id="voiceStatus" style="
                        padding: 10px; 
                        margin: 10px 0; 
                        border-radius: 8px; 
                        background: #f8f9fa; 
                        color: #495057;
                        font-weight: 500;
                    ">Click the button above to ask a question</div>
                </div>
                
                <div style="margin-top: 15px;">
                    <textarea id="questionInput" placeholder="Or type your question here..." style="
                        width: 100%; 
                        height: 80px; 
                        padding: 10px; 
                        border: 2px solid #dee2e6; 
                        border-radius: 8px; 
                        font-size: 14px;
                        resize: vertical;
                    "></textarea>
                    
                    <button id="submitBtn" style="
                        padding: 8px 16px; 
                        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%); 
                        color: white; 
                        border: none; 
                        border-radius: 5px; 
                        cursor: pointer;
                        font-size: 14px;
                        margin-top: 10px;
                    ">🔍 Get Answer</button>
                </div>
                
                <div id="answerArea" style="
                    margin-top: 15px; 
                    padding: 15px; 
                    background: #f8f9fa; 
                    border-radius: 8px; 
                    display: none;
                ">
                    <h5 style="color: #2c3e50; margin-bottom: 10px;">💡 Answer</h5>
                    <div id="answerText" style="color: #495057; line-height: 1.6;"></div>
                </div>
            </div>
            
            <script>
                const voiceBtn = document.getElementById("voiceBtn");
                const voiceStatus = document.getElementById("voiceStatus");
                const questionInput = document.getElementById("questionInput");
                const submitBtn = document.getElementById("submitBtn");
                const answerArea = document.getElementById("answerArea");
                const answerText = document.getElementById("answerText");
                
                let recognition = null;
                
                // Initialize speech recognition
                if ('webkitSpeechRecognition' in window) {
                    recognition = new webkitSpeechRecognition();
                } else if ('SpeechRecognition' in window) {
                    recognition = new SpeechRecognition();
                }
                
                if (recognition) {
                    recognition.continuous = false;
                    recognition.lang = 'en-US';
                    recognition.interimResults = false;
                    
                    recognition.onstart = function() {
                        voiceStatus.innerText = "🎙 Listening... Speak your question!";
                        voiceStatus.style.background = "#fff3cd";
                        voiceStatus.style.color = "#856404";
                        voiceBtn.textContent = "⏹ Stop";
                    };
                    
                    recognition.onresult = function(event) {
                        const question = event.results[0][0].transcript;
                        questionInput.value = question;
                        voiceStatus.innerText = "✅ Question captured: " + question;
                        voiceStatus.style.background = "#d4edda";
                        voiceStatus.style.color = "#155724";
                        
                        // Auto-submit the question
                        setTimeout(() => {
                            submitQuestion(question);
                        }, 1000);
                    };
                    
                    recognition.onerror = function(event) {
                        voiceStatus.innerText = "❌ Error: " + event.error;
                        voiceStatus.style.background = "#f8d7da";
                        voiceStatus.style.color = "#721c24";
                    };
                    
                    recognition.onend = function() {
                        voiceBtn.textContent = "🎤 Ask Question";
                    };
                    
                    voiceBtn.onclick = function() {
                        if (recognition.state === 'recording') {
                            recognition.stop();
                        } else {
                            navigator.mediaDevices.getUserMedia({ audio: true })
                                .then(function(stream) {
                                    stream.getTracks().forEach(track => track.stop());
                                    recognition.start();
                                })
                                .catch(function(err) {
                                    voiceStatus.innerText = "❌ Microphone access denied";
                                    voiceStatus.style.background = "#f8d7da";
                                    voiceStatus.style.color = "#721c24";
                                });
                        }
                    };
                } else {
                    voiceStatus.innerText = "❌ Speech recognition not supported";
                    voiceStatus.style.background = "#f8d7da";
                    voiceStatus.style.color = "#721c24";
                    voiceBtn.disabled = true;
                }
                
                // Handle manual question submission
                submitBtn.onclick = function() {
                    const question = questionInput.value.trim();
                    if (question) {
                        submitQuestion(question);
                    }
                };
                
                function submitQuestion(question) {
                    // Show loading state
                    answerText.innerText = "🔍 Searching for answer...";
                    answerArea.style.display = "block";
                    
                    // Simulate API call (in real implementation, this would call your backend)
                    setTimeout(() => {
                        const mockAnswer = "This is a mock answer for demonstration. In the real implementation, this would be generated by the RAG engine based on the news content and your question.";
                        answerText.innerText = mockAnswer;
                        
                        // Send to Streamlit
                        if (window.parent && window.parent.postMessage) {
                            window.parent.postMessage({
                                type: "question_answered",
                                question: question,
                                answer: mockAnswer
                            }, "*");
                        }
                    }, 2000);
                }
                
                // Handle Enter key in textarea
                questionInput.addEventListener("keypress", function(event) {
                    if (event.key === "Enter" && !event.shiftKey) {
                        event.preventDefault();
                        submitBtn.click();
                    }
                });
            </script>
            """
            
            logger.info("Created voice interaction UI")
            return html_content
            
        except Exception as e:
            logger.error(f"Error creating voice interaction UI: {str(e)}")
            return f"""
            <div style="color: red; padding: 10px; border: 1px solid red; border-radius: 5px;">
                ❌ Error creating voice interaction UI: {str(e)}
            </div>
            """
    
    def create_daily_podcast_player(self, podcast_data: Dict) -> str:
        """
        Create a daily podcast player
        
        Args:
            podcast_data (Dict): Podcast data
            
        Returns:
            str: HTML podcast player
        """
        try:
            title = podcast_data.get("title", "Daily News Podcast")
            duration = podcast_data.get("duration", "5:00")
            summary = podcast_data.get("summary", "")
            
            html_content = f"""
            <div style="margin: 20px 0; padding: 20px; background: linear-gradient(145deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white;">
                <h4 style="margin-bottom: 15px;">📻 Daily News Podcast</h4>
                
                <div style="margin-bottom: 15px;">
                    <h5 style="margin-bottom: 10px;">{title}</h5>
                    <p style="opacity: 0.9; margin-bottom: 10px;">Duration: {duration}</p>
                    <p style="opacity: 0.9; line-height: 1.6;">{summary}</p>
                </div>
                
                <div style="margin: 20px 0;">
                    <audio controls style="width: 100%; height: 40px;">
                        <source src="data:audio/mp3;base64," type="audio/mp3">
                        Your browser does not support the audio element.
                    </audio>
                </div>
                
                <div style="margin-top: 15px;">
                    <button onclick="downloadPodcast()" style="
                        padding: 8px 16px; 
                        background: rgba(255, 255, 255, 0.2); 
                        color: white; 
                        border: 1px solid rgba(255, 255, 255, 0.3); 
                        border-radius: 5px; 
                        cursor: pointer;
                        font-size: 14px;
                    ">📥 Download Podcast</button>
                </div>
            </div>
            
            <script>
            function downloadPodcast() {{
                // Mock download functionality
                alert("Download feature coming soon!");
            }}
            </script>
            """
            
            logger.info("Created daily podcast player")
            return html_content
            
        except Exception as e:
            logger.error(f"Error creating podcast player: {str(e)}")
            return f"""
            <div style="color: red; padding: 10px; border: 1px solid red; border-radius: 5px;">
                ❌ Error creating podcast player: {str(e)}
            </div>
            """
    
    def create_quiz_player(self, quiz_data: Dict) -> str:
        """
        Create a quiz player for MCQs
        
        Args:
            quiz_data (Dict): Quiz data
            
        Returns:
            str: HTML quiz player
        """
        try:
            questions = quiz_data.get("questions", [])
            
            if not questions:
                return """
                <div style="color: #856404; padding: 10px; border: 1px solid #ffeaa7; border-radius: 5px; background: #fff3cd;">
                    No quiz questions available.
                </div>
                """
            
            html_content = """
            <div style="margin: 20px 0; padding: 20px; background: linear-gradient(145deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 15px; border-left: 4px solid #28a745;">
                <h4 style="color: #2c3e50; margin-bottom: 15px;">🧠 Smart Quiz</h4>
            """
            
            for i, question in enumerate(questions):
                question_text = question.get("question", "")
                options = question.get("options", [])
                correct_answer = question.get("correct_answer", 0)
                explanation = question.get("explanation", "")
                
                html_content += f"""
                <div style="margin-bottom: 20px; padding: 15px; background: white; border-radius: 8px; border: 1px solid #dee2e6;">
                    <h5 style="color: #495057; margin-bottom: 10px;">{question_text}</h5>
                    
                    <div style="margin-bottom: 10px;">
                """
                
                for j, option in enumerate(options):
                    option_letter = chr(65 + j)  # A, B, C, D
                    html_content += f"""
                        <div style="margin: 5px 0;">
                            <input type="radio" name="q{i}" id="q{i}opt{j}" value="{j}">
                            <label for="q{i}opt{j}" style="margin-left: 5px; color: #495057;">{option_letter}) {option}</label>
                        </div>
                    """
                
                html_content += f"""
                    </div>
                    
                    <button onclick="checkAnswer({i}, {correct_answer})" style="
                        padding: 5px 10px; 
                        background: linear-gradient(135deg, #007bff 0%, #0056b3 100%); 
                        color: white; 
                        border: none; 
                        border-radius: 3px; 
                        cursor: pointer;
                        font-size: 12px;
                    ">Check Answer</button>
                    
                    <div id="result{i}" style="margin-top: 10px; display: none;"></div>
                    <div id="explanation{i}" style="margin-top: 10px; padding: 10px; background: #e8f4fd; border-radius: 5px; display: none; color: #0c5460; font-size: 14px;">
                        {explanation}
                    </div>
                </div>
                """
            
            html_content += """
            </div>
            
            <script>
            function checkAnswer(questionIndex, correctAnswer) {
                const selectedOption = document.querySelector(`input[name="q${questionIndex}"]:checked`);
                const resultDiv = document.getElementById(`result${questionIndex}`);
                const explanationDiv = document.getElementById(`explanation${questionIndex}`);
                
                if (!selectedOption) {
                    resultDiv.innerHTML = "Please select an answer first.";
                    resultDiv.style.display = "block";
                    resultDiv.style.color = "#856404";
                    resultDiv.style.background = "#fff3cd";
                    resultDiv.style.padding = "5px";
                    resultDiv.style.borderRadius = "3px";
                    return;
                }
                
                const selectedAnswer = parseInt(selectedOption.value);
                const isCorrect = selectedAnswer === correctAnswer;
                
                if (isCorrect) {
                    resultDiv.innerHTML = "✅ Correct!";
                    resultDiv.style.color = "#155724";
                    resultDiv.style.background = "#d4edda";
                } else {
                    resultDiv.innerHTML = "❌ Incorrect. The correct answer is highlighted.";
                    resultDiv.style.color = "#721c24";
                    resultDiv.style.background = "#f8d7da";
                    
                    // Highlight correct answer
                    const correctOption = document.querySelector(`input[name="q${questionIndex}"][value="${correctAnswer}"]`);
                    if (correctOption) {
                        correctOption.nextElementSibling.style.color = "#28a745";
                        correctOption.nextElementSibling.style.fontWeight = "bold";
                    }
                }
                
                resultDiv.style.display = "block";
                resultDiv.style.padding = "5px";
                resultDiv.style.borderRadius = "3px";
                explanationDiv.style.display = "block";
            }
            </script>
            """
            
            logger.info(f"Created quiz player with {len(questions)} questions")
            return html_content
            
        except Exception as e:
            logger.error(f"Error creating quiz player: {str(e)}")
            return f"""
            <div style="color: red; padding: 10px; border: 1px solid red; border-radius: 5px;">
                ❌ Error creating quiz player: {str(e)}
            </div>
            """ 