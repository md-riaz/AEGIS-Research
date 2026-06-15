import asyncio
import json
from aegis.server.intent_parser import IntentParser
from aegis.server.mapper import SemanticMapper
from aegis.server.compiler import SQLCompiler

# Configuration
API_KEY = os.getenv("GROQ_API_KEY")
MODEL = "gpt-oss:120b"

async def debug_queries():
    parser = IntentParser(api_key=API_KEY, models=[MODEL])
    mapper = SemanticMapper()
    compiler = SQLCompiler()
    
    queries = [
        "How many orders were placed yesterday?",
        "How many new customers signed up this morning?"
    ]
    
    for q in queries:
        print(f"\nQUERY: {q}")
        try:
            intent = await parser.parse(q)
            print(f"INTENT: {intent.model_dump_json(indent=2)}")
            plan = mapper.map(intent)
            print(f"PLAN: {plan.model_dump_json(indent=2)}")
            sql = compiler.compile(plan)
            print(f"SQL: {sql}")
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_queries())
