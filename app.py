import streamlit as st
import requests
from bs4 import BeautifulSoup
import os
import re
import random
from collections import Counter
import nltk

nltk.download('punkt')
nltk.download('stopwords')

# ---------------- CONFIG ---------------- #
HF_API_TOKEN = st.secrets.get("HF_API_TOKEN", "")
HF_MODEL = "sshleifer/distilbart-cnn-12-6"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9"
}

IMAGE_DIR = "downloaded_images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# ---------------- 20 SOURCES ---------------- #
SOURCES = [
    ("Guardian", "https://www.theguardian.com/football"),
    ("BBC", "https://www.bbc.com/sport/football"),
    ("ESPN", "https://www.espn.com/soccer/"),
    ("Goal", "https://www.goal.com/en"),
    ("Sky Sports", "https://www.skysports.com/football"),
    ("Football365", "https://www.football365.com"),
    ("The Athletic", "https://theathletic.com/football/"),
    ("CBS Sports", "https://www.cbssports.com/soccer/"),
    ("NBC Sports", "https://www.nbcsports.com/soccer"),
    ("Yahoo Sports", "https://sports.yahoo.com/soccer/"),
    ("Fox Sports", "https://www.foxsports.com/soccer"),
    ("Bleacher Report", "https://bleacherreport.com/world-football"),
    ("90min", "https://www.90min.com"),
    ("GiveMeSport", "https://www.givemesport.com/football"),
    ("TalkSport", "https://talksport.com/football"),
    ("Mirror Football", "https://www.mirror.co.uk/sport/football/"),
    ("Independent", "https://www.independent.co.uk/sport/football"),
    ("Evening Standard", "https://www.standard.co.uk/sport/football"),
    ("Reuters Sports", "https://www.reuters.com/lifestyle/sports/"),
    ("AP News", "https://apnews.com/hub/soccer")
]

# Session state for rotating sources
if "source_index" not in st.session_state:
    st.session_state.source_index = 1

# ---------------- HUGGING FACE ---------------- #
def summarize_hf(text):
    try:
        API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

        payload = {
            "inputs": text[:2000],
            "parameters": {"max_length": 80, "min_length": 30}
        }

        res = requests.post(API_URL, headers=headers, json=payload, timeout=20)

        if res.status_code != 200:
            return "⚠️ HF API Error"

        result = res.json()
        return result[0]["summary_text"] if isinstance(result, list) else "No summary"

    except:
        return "Summary failed"

# ---------------- GENERIC SCRAPER ---------------- #
def extract_links(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            text = a.get_text(strip=True)

            if len(text) > 30 and "http" in href:
                links.append((text, href))

        return links[:5]

    except:
        return []

def scrape_article(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text() for p in paragraphs[:30])

        img_tag = soup.find("meta", property="og:image")
        image_url = img_tag["content"] if img_tag else None

        return text, image_url

    except:
        return "", None

# ---------------- HASHTAGS ---------------- #
def generate_hashtags(text):
    try:
        words = re.findall(r"\b[A-Za-z]{4,}\b", text.lower())
        stopwords = set(nltk.corpus.stopwords.words("english"))

        filtered = [w for w in words if w not in stopwords]
        common = Counter(filtered).most_common(5)

        return [f"#{w.capitalize()}" for w, _ in common]

    except:
        return ["#Football", "#Soccer"]

# ---------------- IMAGE ---------------- #
def download_image(url, title):
    if not url:
        return None
    try:
        res = requests.get(url, headers=HEADERS)
        filename = re.sub(r'[\\/*?:"<>|]', "", title)[:50] + ".jpg"
        path = os.path.join(IMAGE_DIR, filename)
        with open(path, "wb") as f:
            f.write(res.content)
        return path
    except:
        return None

# ---------------- UI ---------------- #
st.set_page_config(page_title="⚽ Multi-Source Soccer AI", layout="wide")

st.title("⚽ Multi-Source Soccer News AI")
st.caption("20 Sources • Auto Rotation • AI Summaries")

if st.button("🚀 Fetch News"):
    max_sources = st.session_state.source_index

    st.info(f"Using {max_sources} source(s)")

    active_sources = SOURCES[:max_sources]

    for name, url in active_sources:
        st.divider()
        st.subheader(f"🌍 Source: {name}")

        articles = extract_links(url)

        if not articles:
            st.warning("No articles found")
            continue

        for title, link in articles[:2]:
            st.markdown(f"### {title}")

            text, image_url = scrape_article(link)

            if not text or len(text) < 200:
                st.warning("⚠️ Content blocked/skipped")
                continue

            summary = summarize_hf(text)
            hashtags = generate_hashtags(text)

            if image_url:
                st.image(image_url, use_container_width=True)

            post = f"""
🔥 {title}

📝 {summary}

🔗 {link}

{' '.join(hashtags)}
"""

            st.text_area("📋 Copy Post", post, height=150)

    # 🔥 Increase sources each refresh
    if st.session_state.source_index < len(SOURCES):
        st.session_state.source_index += 1
        
