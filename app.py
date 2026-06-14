import os

from flask import Flask, render_template, request

from config import DATA_FILE, SEED_URLS
from crawler import load_crawled_data, simple_web_crawler_with_storage
from search_engine import build_inverted_index, search_index
from llm_client import call_gemini_llm

app = Flask(__name__)

crawled_pages = []
crawled_data_map = {}
inverted_index = {}


def initialize_search_agent(force_re_crawl=False):
    global crawled_pages, crawled_data_map, inverted_index

    if force_re_crawl:
        import os as _os
        if _os.path.exists(DATA_FILE):
            print("Force re-crawl enabled: Deleting existing 'my_search_data.json'...")
            _os.remove(DATA_FILE)

    crawled_pages = load_crawled_data(DATA_FILE)

    if not crawled_pages:
        print("No existing crawled data found or data is empty. Running a small initial crawl...")
        crawled_pages = simple_web_crawler_with_storage(SEED_URLS, max_pages=10, delay=1, output_file=DATA_FILE)
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
            llm_context = ""
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
