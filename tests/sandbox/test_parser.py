import asyncio
import json
from safedash.server.intent_parser import IntentParser

async def test():
    parser = IntentParser()
    queries = [
        "What was the total revenue generated today?",
        "How many orders were placed yesterday?",
        "Which 10 products have the highest profit margin this month?"
    ]
    
    for q in queries:
        print(f"\nQuery: {q}")
        try:
            intent = await parser.parse(q)
            print(f"Success: {intent.intent_class}")
            print(f"Filters: {intent.filters}")
        except Exception as e:
            print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test())
