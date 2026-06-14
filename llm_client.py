import time

import requests

from config import GEMINI_API_KEY, GEMINI_API_URL


def call_gemini_llm(prompt_text):
    if not GEMINI_API_KEY:
        return "AI is not configured (missing API key)."

    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt_text}]}]
    }

    retries = 0
    max_retries = 5
    while retries < max_retries:
        try:
            response = requests.post(
                f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                headers=headers, json=payload, timeout=30
            )
            response.raise_for_status()
            result = response.json()

            if result.get('candidates') and result['candidates'][0].get('content') and result['candidates'][0]['content'].get('parts'):
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                print(f"LLM response structure unexpected: {result}")
                return "Could not generate a response from the AI."
        except requests.exceptions.RequestException as e:
            retries += 1
            if retries >= max_retries:
                print(f"LLM API call failed (attempt {retries}/{max_retries}): {e}. No more retries.")
                break
            wait_time = 2 ** retries
            print(f"LLM API call failed (attempt {retries}/{max_retries}): {e}. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
        except Exception as e:
            print(f"An unexpected error occurred during LLM call: {e}")
            return "An error occurred while generating AI response."
    return "Failed to get a response from the AI after multiple retries."
