import streamlit as st
import streamlit.components.v1 as components
from rag_engine import get_rag_response

st.set_page_config(page_title="EchoNews", layout="centered")

st.title("🗣️ EchoNews - Voice Query News Assistant")
st.markdown("### 🎤 Speak your news query below")

# JavaScript Mic + STT
components.html(
    """
    <html>
    <body>
        <button id="start" style="padding:10px; font-size:16px;">🎙 Start Recording</button>
        <p id="status">Press and speak your query.</p>
        <textarea id="output" rows="4" cols="50" style="width:100%; padding:10px;"></textarea>

        <script>
            const startButton = document.getElementById("start");
            const output = document.getElementById("output");
            const status = document.getElementById("status");

            let recognition;
            if ('webkitSpeechRecognition' in window) {
                recognition = new webkitSpeechRecognition();
            } else {
                status.innerText = "❌ Browser doesn't support speech recognition.";
            }

            if (recognition) {
                recognition.continuous = false;
                recognition.lang = 'en-US';
                recognition.interimResults = false;

                recognition.onstart = function () {
                    status.innerText = "🎙 Listening...";
                };

                recognition.onresult = function (event) {
                    const transcript = event.results[0][0].transcript;
                    output.value = transcript;
                    window.parent.postMessage({ type: 'FROM_MIC', text: transcript }, '*');
                    status.innerText = "✅ Done";
                };

                recognition.onerror = function (event) {
                    status.innerText = '❌ Error: ' + event.error;
                };

                recognition.onend = function () {
                    status.innerText += " | Click again to retry.";
                };

                startButton.onclick = () => recognition.start();
            }
        </script>
    </body>
    </html>
    """,
    height=300,
)

# Capture query
st.markdown("### 📝 Or type your query manually")
query = st.text_input("Enter your query", "")

# Sync with JS
query_holder = st.empty()
st.markdown("<script>window.addEventListener('message', (event) => { if(event.data.type === 'FROM_MIC'){ window.parent.postMessage({ isStreamlitMessage: true, type: 'streamlit:setComponentValue', value: event.data.text }, '*'); } });</script>", unsafe_allow_html=True)

if query:
    st.success(f"Query: {query}")
    response = get_rag_response(query)
    st.markdown("### 📰 Response")
    st.write(response)
