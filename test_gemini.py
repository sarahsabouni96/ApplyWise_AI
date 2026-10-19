import os
from google import genai

key = os.getenv("GEMINI_API_KEY")
print("API key loaded:", bool(key))

client = genai.Client(api_key=key)

try:
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents="Reply with just: Hello Sarah!"
    )
    print(response.text)
except Exception as e:
    print("Error type:", type(e).__name__)
    print("Error details:", str(e)[:1500])
