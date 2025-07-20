import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def ask_gemini(question):
    model = genai.GenerativeModel('gemini-2.5-flash')
    response = model.generate_content(question)
    return response.text
