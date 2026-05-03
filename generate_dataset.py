import json
import httpx
import os

def generate_questions():
    # Only use OpenRouter (GLM 4.5 Air Free) as requested
    api_key_or = os.getenv("OPENROUTER_API_KEY")
    url_or = "https://openrouter.ai/api/v1/chat/completions"
    model_or = "openai/gpt-oss-120b:free"
    
    prompt = """
Generate 100 diverse natural language reporting questions for an ecommerce store (nopCommerce).
The questions should cover 6 categories:
1. KPI Lookup (e.g., "What was the total revenue today?")
2. Ranking (e.g., "Who are the top 10 customers by spending?")
3. Trend Analysis (e.g., "Show sales by month for 2023")
4. Comparison (e.g., "Compare sales between Electronics and Apparel")
5. Exception Reporting (e.g., "List products with stock less than 10")
6. Multi-metric Summary (e.g., "Give me an overview of product category performance")

Return the result as a JSON object with a key 'questions' which is a list of strings.
"""
    
    print(f"Trying OpenRouter ({model_or})...")
    try:
        response = httpx.post(
            url_or,
            headers={"Authorization": f"Bearer {api_key_or}"},
            json={
                "model": model_or,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=60.0
        )
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            
            # Remove markdown JSON wrapping if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            # Find the first { and last } to be extra safe
            start = content.find('{')
            end = content.rfind('}')
            if start != -1 and end != -1:
                content = content[start:end+1]
            
            questions_data = json.loads(content)
            questions = questions_data.get('questions', [])
            
            if questions:
                with open("questions.json", "w") as f:
                    json.dump(questions, f, indent=2)
                print(f"Successfully generated {len(questions)} questions using OpenRouter.")
                return
            else:
                print("Error: No questions found in the JSON response.")
        else:
            print(f"OpenRouter failed with status {response.status_code}: {response.text}")

    except Exception as e:
        print(f"OpenRouter exception: {e}")

if __name__ == "__main__":
    generate_questions()
