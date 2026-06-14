import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
DATA_FILE = "my_search_data.json"
INDEX_FILE = "search_index.json"

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY environment variable not set. AI features will fail.")

USER_AGENT = "AI-Search-Agent/1.0 (Educational)"

RESULTS_PER_PAGE = 10
MAX_PAGES = 50

SEED_URLS = [
    "https://www.themessycorner.in/",
    "https://indianexpress.com/",
    "https://www.cricbuzz.com/"
]

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he",
    "in", "is", "it", "its", "of", "on", "that", "the", "to", "was", "were", "will", "with"
}
