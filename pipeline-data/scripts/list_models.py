import os
import google.generativeai as genai
from dotenv import load_dotenv

from pathlib import Path

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
api_key = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

for m in genai.list_models():
    if "generateContent" in m.supported_generation_methods:
        print(m.name)
