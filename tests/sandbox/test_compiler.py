import asyncio
import os
from safedash.server.intent_parser import IntentParser
from safedash.server.mapper import SemanticMapper
from safedash.server.compiler import SQLCompiler
from safedash.server.models import AnalysisPlan

async def test():
    parser = IntentParser()
    mapper = SemanticMapper()
    compiler = SQLCompiler()
    
    test_queries = [
        "What was the total revenue generated today?",
        "List the top 7 most frequently purchased categories this quarter.",
        "Compare sales between Electronics and Apparel."
    ]
    
    for q in test_queries:
        print(f"\nQuery: {q}")
        try:
            intent = await parser.parse(q)
            print(f"Intent: {intent.model_dump_json(indent=2)}")
            plan = mapper.map(intent)
            print(f"Plan: {plan.model_dump_json(indent=2)}")
            sql = compiler.compile(plan)
            print(f"SQL:\n{sql}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
