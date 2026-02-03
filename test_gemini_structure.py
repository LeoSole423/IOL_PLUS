import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-preview:generateContent?key={api_key}"

headers = {'Content-Type': 'application/json'}
data = {
    "contents": [{"parts": [{"text": "Explain why the sky is blue."}]}],
    "generationConfig": {
        "thinkingConfig": {
            "includeThoughts": True
        }
    }
}

try:
    print("Sending request...")
    response = requests.post(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(json.dumps(result, indent=2))
    else:
        print(response.text)
        
except Exception as e:
    print(e)
