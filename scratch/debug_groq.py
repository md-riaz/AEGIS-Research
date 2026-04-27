import os
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

async def debug_groq():
    api_key = os.getenv("GROQ_API_KEY")
    url = "https://api.groq.com/openai/v1/chat/completions"
    model = "llama-3.1-8b-instant"
    
    system_prompt = """
    You are the Intent Extraction Engine for SafeDash, a governed BI system.
    Your ONLY role is to translate a user's natural language reporting request into a structured JSON 'Intent' object.
    
    JSON SCHEMA:
    {
      "intent_class": "kpi|ranking|trend|comparison|exception|summary|point_lookup",
      "metric_term": "string (e.g., 'revenue', 'order_count', 'refund_amount')",
      "dimension_term": "string or null (e.g., 'category', 'customer', 'status')",
      "filters": [{"field": "string", "operator": "=|!=|>|<|>=|<=|contains|is_null", "value": "any"}],
      "sort": "asc|desc|null",
      "limit": "integer|null"
    }
    
    EXAMPLES:
    - 'Top 5 products by sales' -> {"intent_class": "ranking", "metric_term": "revenue", "dimension_term": "product", "limit": 5, "sort": "desc"}
    - 'Orders above 200' -> {"intent_class": "kpi", "filters": [{"field": "order_total", "operator": ">", "value": 200}]}
    - 'Sales in April' -> {"intent_class": "trend", "time_term": "April 2024"}
    
    CRITICAL: Return ONLY raw JSON. No markdown blocks. No explanations.
    """
    
    prompt = "How many new customers signed up this morning?"
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"}
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout=45.0
        )
        print(f"Status: {response.status_code}")
        print(f"Body: {response.text}")

if __name__ == "__main__":
    asyncio.run(debug_groq())
