import streamlit as st
import streamlit.components.v1 as components
import time

st.set_page_config(page_title="EchoNews", layout="centered")

st.title("🗣️ EchoNews - Voice Query News Assistant")

st.markdown("### 🎤 Speak your news query below")

# JavaScript mic + speech-to-text (browser-based)
components.html(
    """
    <html>
    <body>
        <button id="start" style="padding:10px; font-size:16px;">🎙 Start Recording</button>
        <p id="status">Press "Start Recording" and speak your query.</p>
        <textarea id="output" rows="4" cols="50" style="width:100%; padding:10px;"></textarea>

        <script>
            const startButton = document.getElementById("start");
            const output = document.getElementById("output");
            const status = document.getElementById("status");

            let recognition;
            if ('webkitSpeechRecognition' in window) {
                recognition = new webkitSpeechRecognition();
            } else {
                status.innerText = "Your browser does not support speech recognition.";
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

                    // Streamlit - send text to Python
                    const streamlitInput = window.parent.document.querySelector('iframe[title="streamlit_app"]').contentWindow;
                    streamlitInput.postMessage({isStreamlitMessage: true, type: "streamlit:setComponentValue", value: transcript}, "*");

                    status.innerText = "✅ Done";
                };

                recognition.onerror = function (event) {
                    status.innerText = 'Error occurred: ' + event.error;
                };

                recognition.onend = function () {
                    status.innerText += " | You can speak again.";
                };

                startButton.onclick = () => {
                    recognition.start();
                };
            }
        </script>
    </body>
    </html>
    """,
    height=300,
)

# Now add a manual text box in case audio fails
st.markdown("### 📝 Or type your query manually")
query = st.text_input("Enter your query", "")

if query:
    st.success(f"Query received: {query}")
    # Now pass this to your RAG system
    # Example: response = rag_engine.get_answer(query)
    # st.write(response)
