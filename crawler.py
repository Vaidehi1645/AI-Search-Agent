import json
import os
import random
import time
from collections import deque
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from config import DATA_FILE, SEED_URLS, USER_AGENT

_robot_parsers = {}


def _get_robot_parser(domain):
    if domain not in _robot_parsers:
        parser = RobotFileParser()
        parser.set_url(f"https://{domain}/robots.txt")
        try:
            parser.read()
        except Exception:
            pass
        _robot_parsers[domain] = parser
    return _robot_parsers[domain]


def _can_fetch(url):
    parsed = urlparse(url)
    domain = parsed.netloc
    parser = _get_robot_parser(domain)
    return parser.can_fetch(USER_AGENT, url)


def _extract_main_content(html, url):
    try:
        import trafilatura
        text = trafilatura.extract(
            html, output_format='txt',
            include_links=False, include_images=False,
            include_tables=False, include_comments=False
        )
        if text and text.strip():
            return text.strip()
    except Exception:
        pass
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text(separator=' ', strip=True)


def _extract_meta_description(html):
    soup = BeautifulSoup(html, 'html.parser')
    tag = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
    if tag and tag.get('content'):
        return tag['content'].strip()
    return None


def _extract_title(html):
    soup = BeautifulSoup(html, 'html.parser')
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    return None


def fetch_webpage(url):
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': USER_AGENT})
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def parse_webpage(html_content, base_url):
    soup = BeautifulSoup(html_content, 'html.parser')
    links = []
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        from urllib.parse import urljoin
        absolute_url = urljoin(base_url, href)
        parsed_url = urlparse(absolute_url)
        if parsed_url.scheme in ['http', 'https'] and parsed_url.netloc:
            links.append(absolute_url)
    return {"links": list(set(links))}


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

        if not _can_fetch(current_url):
            print(f"Skipping (robots.txt): {current_url}")
            visited_urls.add(current_url)
            continue

        print(f"Crawling: {current_url} ({len(crawled_data) + 1}/{max_pages})")
        html_content = fetch_webpage(current_url)
        visited_urls.add(current_url)

        if html_content:
            page_text = _extract_main_content(html_content, current_url)
            meta_desc = _extract_meta_description(html_content)
            title = _extract_title(html_content)

            crawled_data.append({
                "url": current_url,
                "text": page_text,
                "meta_description": meta_desc,
                "title": title
            })

            parsed_info = parse_webpage(html_content, current_url)
            current_domain = urlparse(current_url).netloc
            for link in parsed_info["links"]:
                if link not in visited_urls:
                    if urlparse(link).netloc == current_domain:
                        urls_to_visit.appendleft(link)
                    else:
                        urls_to_visit.append(link)
        else:
            crawled_data.append({
                "url": current_url,
                "text": "",
                "meta_description": None,
                "title": current_url
            })

        jitter = random.uniform(0.5, 1.5)
        time.sleep(delay * jitter)

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
