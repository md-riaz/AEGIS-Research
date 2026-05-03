import asyncio
import httpx

GROQ_KEY = "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"
URL = "https://api.groq.com/openai/v1/chat/completions"

async def test_groq_sql():
    prompt = "Given nopCommerce schema (Order, Product, Customer), write SQL for: Total revenue today. Return ONLY SQL."
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            URL,
            headers={"Authorization": f"Bearer {GROQ_KEY}"},
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1
            }
        )
        print(f"GROQ SQL:\n{response.json()['choices'][0]['message']['content']}")

if __name__ == "__main__":
    asyncio.run(test_groq_sql())
