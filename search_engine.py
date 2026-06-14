import json
import math
import os
import re
from collections import defaultdict

from config import INDEX_FILE, RESULTS_PER_PAGE, STOP_WORDS


def normalize_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    words = text.split()
    return [word for word in words if word not in STOP_WORDS and len(word) > 1]


def build_inverted_index(crawled_data):
    inverted_index = {}
    doc_count = len(crawled_data)
    print("Building inverted index with TF...")
    for page in crawled_data:
        url = page['url']
        text = page.get('text', '')
        words = normalize_text(text)
        word_counts = defaultdict(int)
        for word in words:
            word_counts[word] += 1
        for word, count in word_counts.items():
            inverted_index.setdefault(word, {})[url] = count
    save_index_meta({"doc_count": doc_count})
    print(f"Inverted index built with {len(inverted_index)} unique terms across {doc_count} documents.")
    return inverted_index


def save_index_meta(meta, output_file="search_meta.json"):
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False)
    except IOError as e:
        print(f"Error saving meta: {e}")


def load_index_meta(input_file="search_meta.json"):
    if not os.path.exists(input_file):
        return {}
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


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


def _compute_tfidf(query_words, inverted_index, crawled_data_map, doc_count):
    scores = defaultdict(float)

    for word in query_words:
        postings = inverted_index.get(word)
        if not postings:
            continue

        df = len(postings)
        idf = math.log((doc_count + 1) / (df + 1)) + 1

        for url, tf_raw in postings.items():
            page = crawled_data_map.get(url, {})
            total_terms = len(normalize_text(page.get('text', '')))
            tf = tf_raw / max(total_terms, 1)
            scores[url] += tf * idf

    return scores


def _generate_snippet(url, query_words, crawled_data_map, meta_desc):
    if meta_desc:
        return meta_desc

    page = crawled_data_map.get(url, {})
    full_text = page.get('text', '')

    best_snippet = "..."
    best_pos = -1

    for word in query_words:
        for match in re.finditer(r'\b' + re.escape(word) + r'\b', full_text, re.IGNORECASE):
            start = max(0, match.start() - 60)
            end = min(len(full_text), match.end() + 100)
            if start > best_pos:
                best_pos = start
                snippet = full_text[start:end].replace('\n', ' ')
                if start > 0:
                    snippet = "..." + snippet
                if end < len(full_text):
                    snippet = snippet + "..."
                best_snippet = snippet

    return best_snippet


def search_index(query, inverted_index, crawled_data_map, page=1):
    query_words = normalize_text(query)
    if not query_words:
        return [], 0, 0

    meta = load_index_meta()
    doc_count = meta.get("doc_count", len(crawled_data_map))

    scores = _compute_tfidf(query_words, inverted_index, crawled_data_map, doc_count)

    results = []
    for url, score in scores.items():
        page_data = crawled_data_map.get(url, {})
        title = page_data.get('title', url)
        meta_desc = page_data.get('meta_description')
        snippet = _generate_snippet(url, query_words, crawled_data_map, meta_desc)

        results.append({
            "url": url,
            "title": title,
            "snippet": snippet,
            "score": round(score, 4)
        })

    results.sort(key=lambda x: x['score'], reverse=True)

    total_results = len(results)
    start = (page - 1) * RESULTS_PER_PAGE
    end = start + RESULTS_PER_PAGE
    page_results = results[start:end]

    total_pages = max(1, (total_results + RESULTS_PER_PAGE - 1) // RESULTS_PER_PAGE)

    return page_results, total_results, total_pages
