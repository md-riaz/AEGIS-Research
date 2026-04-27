import asyncio
from safedash.server.intent_parser import IntentParser
from safedash.server.mapper import SemanticMapper
from safedash.server.compiler import SQLCompiler
import json

async def test_abandoned():
    parser = IntentParser()
    mapper = SemanticMapper()
    compiler = SQLCompiler()
    
    query = "How many abandoned orders were there yesterday?"
    intent = await parser.parse(query)
    print("--- Intent ---")
    print(intent.model_dump_json(indent=2))
    
    plan = mapper.map(intent)
    print("\n--- Plan ---")
    print(plan.model_dump_json(indent=2))
    
    sql = compiler.compile(plan)
    print("\n--- SQL ---")
    print(sql)

if __name__ == "__main__":
    asyncio.run(test_abandoned())
