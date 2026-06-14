import json
import os
import re
from collections import defaultdict

from config import INDEX_FILE, STOP_WORDS


def normalize_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    words = text.split()
    filtered_words = [word for word in words if word not in STOP_WORDS and len(word) > 1]
    return filtered_words


def build_inverted_index(crawled_data):
    inverted_index = defaultdict(list)
    print("Building inverted index...")
    for page in crawled_data:
        url = page['url']
        text = page.get('text', '')
        words = normalize_text(text)
        for word in set(words):
            inverted_index[word].append(url)
    print(f"Inverted index built with {len(inverted_index)} unique terms.")
    return dict(inverted_index)


def save_inverted_index(index, output_file=INDEX_FILE):
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False)
        print(f"Inverted index saved to '{output_file}'")
    except IOError as e:
        print(f"Error saving index: {e}")


def load_inverted_index(input_file=INDEX_FILE):
    if not os.path.exists(input_file):
        print(f"Index file '{input_file}' not found.")
        return None
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        print(f"Loaded inverted index with {len(index)} terms from '{input_file}'")
        return index
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading index '{input_file}': {e}")
        return None


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
        meta_desc = page_data.get('meta_description')
        title = page_data.get('title', url)

        snippet = meta_desc if meta_desc else "..."
        if not meta_desc:
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
            "title": title,
            "snippet": snippet,
            "score": score
        })

    results.sort(key=lambda x: x['score'], reverse=True)
    return results
