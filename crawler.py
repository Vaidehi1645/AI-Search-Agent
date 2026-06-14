import json
import os
import time
from collections import deque

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

from config import DATA_FILE, SEED_URLS


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


def simple_web_crawler_with_storage(start_urls=None, max_pages=10, delay=1, output_file=DATA_FILE):
    if start_urls is None:
        start_urls = SEED_URLS

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


def load_crawled_data(input_file=DATA_FILE):
    if not os.path.exists(input_file):
        print(f"File '{input_file}' not found. No data to load.")
        return []
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Successfully loaded {len(data)} pages from '{input_file}'")
        return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error reading '{input_file}': {e}")
        return []
