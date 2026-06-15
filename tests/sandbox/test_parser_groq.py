import asyncio
import json
from aegis.server.intent_parser import IntentParser

OLLAMA_KEY = "0737F7C2bbad420989c74f712d0f285a.jNqGqCL_puvJPBgGwQ7kMzxf"
GROQ_KEY = "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"

async def test_parser_with_groq():
    # Test llama-3.3-70b-versatile via Groq
    parser = IntentParser(
        ollama_key=OLLAMA_KEY,
        groq_key=GROQ_KEY,
        models=["llama-3.3-70b-versatile"]
    )
    
    query = "What was the total revenue in Electronics today?"
    print(f"Query: {query}")
    
    try:
        intent = await parser.parse(query)
        print(f"Intent: {intent.model_dump_json(indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_parser_with_groq())
