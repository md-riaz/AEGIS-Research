import asyncio
import httpx
from safedash.server.intent_parser import IntentParser
from safedash.server.ai_config import GROQ_API_KEY, GROQ_URL

async def test_400():
    parser = IntentParser()
    query = "List orders placed with invalid coupon codes in the past week."
    
    # Manually try the post to see the error body
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": parser.SYSTEM_PROMPT},
            {"role": "user", "content": query}
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"}
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            json=payload,
            timeout=10.0
        )
        print(f"Status: {response.status_code}")
        print(f"Body: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_400())
