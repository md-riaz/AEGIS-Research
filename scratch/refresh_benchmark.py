import json
import httpx
import os
import sys

def refresh_benchmark():
    # Only use OpenRouter (GLM 4.5 Air Free) as requested
    api_key_or = "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"
    url_or = "https://openrouter.ai/api/v1/chat/completions"
    model_or = "openai/gpt-oss-120b:free"
    
    if not os.path.exists("questions.json"):
        print("Error: questions.json not found.")
        return

    with open("questions.json", "r", encoding='utf-8') as f:
        original_questions = json.load(f)
    
    # Deduplicate while preserving order
    seen = set()
    unique_questions = []
    for q in original_questions:
        if q not in seen:
            unique_questions.append(q)
            seen.add(q)
    
    current_count = len(unique_questions)
    print(f"Current unique questions: {current_count}")
    
    if current_count >= 100:
        print("Already have 100+ unique questions. Truncating to 100.")
        with open("questions.json", "w", encoding='utf-8') as f:
            json.dump(unique_questions[:100], f, indent=2)
        return

    gap = 100 - current_count
    print(f"Generating {gap} more unique questions...")
    
    prompt = f"""
I have a list of {current_count} unique reporting questions for an ecommerce store (nopCommerce).
I need {gap} more UNIQUE and DIVERSE questions to reach exactly 100 questions.
The total 100 questions must be distributed across these 6 categories:
1. KPI Lookup
2. Ranking
3. Trend Analysis
4. Comparison
5. Exception Reporting
6. Multi-metric Summary

Existing questions (partial list for context):
{json.dumps(unique_questions[:20], indent=2)}

Generate {gap} NEW, non-duplicate questions. 
Return the result as a JSON object with a key 'new_questions' which is a list of strings.
"""
    
    try:
        response = httpx.post(
            url_or,
            headers={"Authorization": f"Bearer {api_key_or}"},
            json={
                "model": model_or,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"}
            },
            timeout=60.0
        )
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            
            # Robust parsing
            try:
                new_data = json.loads(content)
                new_qs = new_data.get('new_questions', [])
                
                # Combine and final dedupe
                final_questions = unique_questions + new_qs
                seen_final = set()
                deduped_final = []
                for q in final_questions:
                    if q not in seen_final:
                        deduped_final.append(q)
                        seen_final.add(q)
                
                print(f"Final count: {len(deduped_final)}")
                
                with open("questions.json", "w", encoding='utf-8') as f:
                    json.dump(deduped_final[:100], f, indent=2)
                
                print(f"Successfully updated questions.json with 100 unique questions.")
            except Exception as e:
                print(f"Failed to parse JSON response: {e}")
                print(f"Raw content: {content}")
        else:
            print(f"API Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    refresh_benchmark()
