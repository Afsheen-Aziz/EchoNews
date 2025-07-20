import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("AIzaSyDC_fKv_iN2Ww98N1jt_UF5dfSmQnctndE"))

models = genai.list_models()
print("Available models:")

for model in models:
    # print all attributes for debugging
    attrs = vars(model)
    print(f"- Name: {getattr(model, 'name', 'N/A')}")
    # Optionally print full attributes for debugging:
    # print(f"  Attributes: {attrs}")
