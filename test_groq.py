import asyncio
import httpx
import json

GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

async def test_groq():
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "user", "content": "Return a JSON object with a 'status' field set to 'success'."}
        ],
        "response_format": {"type": "json_object"}
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(GROQ_URL, headers=headers, json=payload, timeout=30.0)
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print(f"Response: {response.json()['choices'][0]['message']['content']}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_groq())
