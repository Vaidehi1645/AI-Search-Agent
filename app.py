from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from collections import deque, defaultdict
import time
import json
import os
import re

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# --- Global variables for our search agent ---
crawled_pages = []
crawled_data_map = {}
inverted_index = {}

# --- Gemini API Configuration ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY environment variable not set. AI features will fail.")

# --- Helper functions ---

def fetch_webpage(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

def parse_webpage(html_content, base_url):
    soup = BeautifulSoup(html_content, 'html.parser')
    page_text = soup.get_text(separator=' ', strip=True)
    links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        absolute_url = urljoin(base_url, href)
        parsed_url = urlparse(absolute_url)
        if parsed_url.scheme in ['http', 'https'] and parsed_url.netloc:
            links.append(absolute_url)
    return {
        "text": page_text,
        "links": list(set(links))
    }

def simple_web_crawler_with_storage(start_urls, max_pages=50, delay=1, output_file="my_search_data.json"):
    crawled_data = []
    visited_urls = set()
    urls_to_visit = deque(start_urls)

    print(f"Starting crawl with {len(start_urls)} seed URLs...")
    print(f"Data will be saved to '{output_file}'")

    while urls_to_visit and len(crawled_data) < max_pages:
        current_url = urls_to_visit.popleft()

        if current_url in visited_urls:
            continue

        print(f"Crawling: {current_url} ({len(crawled_data) + 1}/{max_pages})")
        html_content = fetch_webpage(current_url)
        visited_urls.add(current_url)

        if html_content:
            parsed_info = parse_webpage(html_content, current_url)
            crawled_data.append({
                "url": current_url,
                "text": parsed_info["text"]
            })

            current_domain = urlparse(current_url).netloc
            for link in parsed_info["links"]:
                if link not in visited_urls:
                    if urlparse(link).netloc == current_domain:
                        urls_to_visit.appendleft(link)
                    else:
                        urls_to_visit.append(link)

        time.sleep(delay)

    print(f"\nCrawl finished. Total pages crawled: {len(crawled_data)}")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(crawled_data, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved crawled data to '{output_file}'")
    except IOError as e:
        print(f"Error saving data to file: {e}")
    return crawled_data

def load_crawled_data(input_file="my_search_data.json"):
    if not os.path.exists(input_file):
        print(f"File '{input_file}' not found. No data to load.")
        return []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Successfully loaded {len(data)} pages from '{input_file}'")
        return data
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from '{input_file}': {e}")
        return []
    except IOError as e:
        print(f"Error reading file '{input_file}': {e}")
        return []

def normalize_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    words = text.split()
    stop_words = set([
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he", "in", "is", "it",
        "its", "of", "on", "that", "the", "to", "was", "were", "will", "with"
    ])
    filtered_words = [word for word in words if word not in stop_words and len(word) > 1]
    return filtered_words

def build_inverted_index(crawled_data):
    inverted_index = defaultdict(list)
    print("Building inverted index...")
    for i, page in enumerate(crawled_data):
        url = page['url']
        text = page['text']
        words = normalize_text(text)
        for word in words:
            if url not in inverted_index[word]:
                inverted_index[word].append(url)
    print(f"Inverted index built with {len(inverted_index)} unique terms.")
    return inverted_index

def search_index(query, inverted_index, crawled_data_map):
    query_words = normalize_text(query)
    candidate_pages = defaultdict(int)

    for word in query_words:
        if word in inverted_index:
            for url in inverted_index[word]:
                candidate_pages[url] += 1
    
    results = []
    for url, score in candidate_pages.items():
        page_data = crawled_data_map.get(url, {})
        full_text = page_data.get('text', '')
        
        snippet = "..."
        for word in query_words:
            if word in full_text:
                match = re.search(r'\b' + re.escape(word) + r'\b', full_text, re.IGNORECASE)
                if match:
                    start_index = max(0, match.start() - 50)
                    end_index = min(len(full_text), match.end() + 100)
                    snippet = full_text[start_index:end_index].replace('\n', ' ')
                    if start_index > 0:
                        snippet = "..." + snippet
                    if end_index < len(full_text):
                        snippet = snippet + "..."
                    break
        
        results.append({
            "url": url,
            "snippet": snippet,
            "score": score,
            "full_text": full_text
        })
    
    results.sort(key=lambda x: x['score'], reverse=True)
    
    return results

# --- New LLM Integration Function ---
def call_gemini_llm(prompt_text):
    """Calls the Gemini LLM API to generate a response."""
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt_text}]}]
    }
    
    # Exponential backoff for API calls
    retries = 0
    max_retries = 5
    while retries < max_retries:
        try:
            response = requests.post(f"{GEMINI_API_URL}?key={GEMINI_API_KEY}", headers=headers, json=payload, timeout=30)
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


# --- Flask Routes ---
def initialize_search_agent(force_re_crawl=False):
    global crawled_pages, crawled_data_map, inverted_index
    
    if force_re_crawl and os.path.exists("my_search_data.json"):
        print("Force re-crawl enabled: Deleting existing 'my_search_data.json'...")
        os.remove("my_search_data.json")

    crawled_pages = load_crawled_data("my_search_data.json")

    if not crawled_pages:
        print("No existing crawled data found or data is empty. Running a small initial crawl...")
        seed_urls = [
            "https://www.themessycorner.in/products/quench-personalised-water-bottle-warm-peach?currency=INR&variant=42346583589036&utm_source=google&utm_medium=cpc&utm_campaign=Google%20Shopping&stkn=206c064cb97a&campaignid=19668131972&adgroupid=&keyword=&device=c&gad_source=1&gad_campaignid=19660251525&gbraid=0AAAAADK-C9SrA1hiGQ2o6-1y0YevKTaCK&gclid=CjwKCAjwy7HEBhBJEiwA5hQNolT9fkvdccLBEAWrsoVqkJpwFmF76ymMtyh0VqEx2Gl-7W5mafv_PxoCrcwQAvD_BwE",
            "https://indianexpress.com/",
            "https://www.cricbuzz.com/"
        ]
        crawled_pages = simple_web_crawler_with_storage(seed_urls, max_pages=10, delay=1, output_file="my_search_data.json")
        if not crawled_pages:
            print("Initial crawl failed to collect data. Search agent will be empty.")
            return

    crawled_data_map = {page['url']: page for page in crawled_pages}
    inverted_index = build_inverted_index(crawled_pages)
    print("Search agent initialized and ready!")

@app.route('/', methods=['GET', 'POST'])
def index():
    query = request.args.get('query', '')
    search_results = []
    ai_response = None
    
    if query:
        print(f"User searched for: '{query}'")
        search_results = search_index(query, inverted_index, crawled_data_map)
        
        if search_results:
            # Prepare context for the LLM from top search results
            llm_context = ""
            # Limit context to avoid token limits and focus on most relevant
            for result in search_results[:3]:
                llm_context += f"--- Document from {result['url']} ---\n"
                llm_context += result['full_text'][:2000] + "\n\n"
            
            if llm_context:
                prompt_for_llm = (
                    f"Based on the following information related to the query '{query}', "
                    f"please provide a concise and direct answer. If the information is insufficient, "
                    f"state that you cannot answer based on the provided context.\n\n"
                    f"Query: {query}\n\n"
                    f"Context:\n{llm_context}"
                    f"Answer:"
                )
                print("Calling LLM for synthesis...")
                ai_response = call_gemini_llm(prompt_for_llm)
                print("LLM response received.")
            else:
                ai_response = "No relevant text found in crawled data to synthesize an AI response."
        else:
            ai_response = "No results found in the local index for your query. Cannot generate an AI response."
    
    return render_template('index.html', query=query, results=search_results, ai_response=ai_response)

if __name__ == '__main__':
    force_re_crawl = os.getenv("FORCE_RE_CRAWL", "false").lower() == "true"
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    initialize_search_agent(force_re_crawl=force_re_crawl)
    app.run(debug=debug_mode)