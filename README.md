# AI Search Agent

An intelligent web search agent that crawls user-provided URLs and answers questions using only the content from those pages. Powered by a custom TF-IDF search engine and Google Gemini for AI-synthesized answers — think of it as a focused Google search limited to the links you care about.

## Why This Was Built

- Generic search engines return results from the entire web, often irrelevant
- Researchers, analysts, and learners often want answers from a curated set of sources
- Manually reading through multiple pages to find answers is slow

**Solution:** Give the agent a list of URLs, and it crawls, indexes, and lets you ask natural-language questions — getting answers synthesized exclusively from your chosen sources.

---

## How It Works

1. **User provides URLs** — The agent asks you for the websites you want to search within
2. **Crawling** — A BFS web crawler fetches pages from those URLs, respects `robots.txt`, extracts main content using `trafilatura`, and stores the data
3. **Indexing** — A TF-IDF inverted index is built from the crawled content for fast retrieval
4. **Searching** — You type a query; the engine finds the most relevant pages using TF-IDF scoring with snippet generation
5. **AI Synthesis** — The top results are passed to Google Gemini 2.0 Flash, which generates a concise, natural-language answer

---

## Key Features

- **Dynamic URL Crawling** — Users provide seed links; the agent crawls and indexes them
- **Custom TF-IDF Search Engine** — Built from scratch with inverted index, scoring, snippets, and pagination
- **AI-Powered Answers** — Google Gemini synthesizes search results into conversational responses
- **Smart Crawling** — BFS traversal, robots.txt compliance, configurable delays with jitter
- **Clean UI** — Single-page interface with Tailwind CSS, keyword highlighting, relevance bars, and loading overlay
- **Result Caching** — In-memory LLM response cache (120s TTL) to avoid redundant API calls
- **Pagination** — 10 results per page with navigation controls

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.11 |
| **Web Framework** | Flask |
| **Crawling** | requests, BeautifulSoup4, trafilatura |
| **Search Engine** | Custom TF-IDF (inverted index, pure Python) |
| **AI / LLM** | Google Gemini 2.0 Flash |
| **Frontend** | Jinja2 + Tailwind CSS (CDN) |
| **Deployment** | Vercel |
| **Storage** | Flat JSON files |

---

## Architecture

```
User → Provides URLs → Crawler → Index Builder → Inverted Index (JSON)
                                                    ↓
User → Types Query → TF-IDF Search → Top Results → LLM (Gemini) → Answer
                                                    ↓
                                              Frontend UI
```

### Module Breakdown

| Module | File | Role |
|---|---|---|
| **Web App** | `app.py` | Flask routes, orchestrates search + LLM, renders UI |
| **Config** | `config.py` | API keys, seed URLs, crawl limits, stop words, all settings |
| **Crawler** | `crawler.py` | BFS web crawler with robots.txt respect, content extraction, JSON persistence |
| **Search Engine** | `search_engine.py` | Inverted index builder, TF-IDF scorer, snippet generator, save/load helpers |
| **LLM Client** | `llm_client.py` | Google Gemini API wrapper with caching, retry logic, and error handling |
| **UI** | `templates/index.html` | Single-page frontend with search, results, AI answer, pagination |

---

## Project Structure

```
AI-Search-Agent/
├── app.py                    # Flask application entry point
├── config.py                 # Central configuration
├── crawler.py                # Web crawler
├── search_engine.py          # TF-IDF search engine
├── llm_client.py             # Google Gemini API client
├── templates/
│   └── index.html            # Frontend UI (Jinja2 + Tailwind CSS)
├── my_search_data.json       # Crawled page data
├── search_index.json         # Inverted index
├── search_meta.json          # Index metadata
├── .env                      # Environment variables
├── .env.example              # Environment template
├── requirements.txt          # Python dependencies
├── vercel.json               # Vercel deployment config
└── README.md                 # This file
```

---

## Getting Started

### Prerequisites

- Python 3.8+
- [Google Gemini API Key](https://ai.google.dev/)

### Installation

```bash
git clone <repo-url>
cd AI-Search-Agent
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and add your Gemini API key:

```env
GEMINI_API_KEY=your_gemini_api_key_here
FLASK_PORT=5000
```

### Run

```bash
python app.py
```

The agent will crawl the provided URLs, build the search index, and start the Flask server at `http://localhost:5000`.

### Usage

1. Open your browser to `http://localhost:5000`
2. Enter seed URLs for the agent to crawl and index
3. Type a search query to see results and an AI-generated answer

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Main search page. Accepts `?query=...&page=...` for queries and pagination |

---

## Deployment

The project includes a `vercel.json` for deployment to [Vercel](https://vercel.com/):

```json
{
  "builds": [{ "src": "app.py", "use": "@vercel/python" }],
  "routes": [{ "src": "/(.*)", "dest": "app.py" }]
}
```

---

## Planned Features

- [ ] Dynamic URL input from the user via the UI
- [ ] Multiple concurrent crawl jobs
- [ ] Support for PDF and document crawling
- [ ] Crawl progress indicators and logs in the UI
- [ ] Export/import of search indexes
- [ ] Customizable crawl depth and page limits

---

## Limitations

- **Flat-file storage** — JSON files are not suitable for large-scale or concurrent use
- **Single-user** — No authentication or session management
- **Educational grade** — Built as a learning resource, not for production

---

## License

ISC
