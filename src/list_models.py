import os
import requests
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("No API Key found in .env")
else:
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            print("Available Models for your Key:")
            for m in data.get('models', []):
                if 'generateContent' in m.get('supportedGenerationMethods', []):
                    print(f"- {m['name']} ({m['version']})")
        else:
            print(f"Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error: {e}")
