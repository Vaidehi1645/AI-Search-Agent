import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
DATA_FILE = "my_search_data.json"

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY environment variable not set. AI features will fail.")

SEED_URLS = [
    "https://www.themessycorner.in/products/quench-personalised-water-bottle-warm-peach?currency=INR&variant=42346583589036&utm_source=google&utm_medium=cpc&utm_campaign=Google%20Shopping&stkn=206c064cb97a&campaignid=19668131972&adgroupid=&keyword=&device=c&gad_source=1&gad_campaignid=19660251525&gbraid=0AAAAADK-C9SrA1hiGQ2o6-1y0YevKTaCK&gclid=CjwKCAjwy7HEBhBJEiwA5hQNolT9fkvdccLBEAWrsoVqkJpwFmF76ymMtyh0VqEx2Gl-7W5mafv_PxoCrcwQAvD_BwE",
    "https://indianexpress.com/",
    "https://www.cricbuzz.com/"
]

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he",
    "in", "is", "it", "its", "of", "on", "that", "the", "to", "was", "were", "will", "with"
}
