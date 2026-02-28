
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Try to read manually if env var missing
if not api_key:
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('GEMINI_API_KEY='):
                    api_key = line.strip().split('=')[1]
                    break
    except:
        pass

genai.configure(api_key=api_key)

candidates = [
    "gemini-1.5-flash",
    "gemini-1.5-flash-001",
    "gemini-1.5-flash-8b",
    "gemini-2.0-flash-exp",
    "gemini-pro",
    "gemini-1.0-pro",
    "gemini-1.5-pro"
]

print(f"Testing models with key: {api_key[:5]}...")

for model_name in candidates:
    print(f"Testing {model_name}...", end=" ")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello")
        print(f"SUCCESS! Response: {response.text[:20]}...")
        print(f"WORKING_MODEL={model_name}")
        break  # features found a working one
    except Exception as e:
        print(f"FAILED. Error: {str(e)[:100]}")
