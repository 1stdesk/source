import streamlit as st
import requests
from bs4 import BeautifulSoup
import os
import re
from collections import Counter
import nltk

# Download NLTK resources
nltk.download('punkt')
nltk.download('stopwords')

# ---------------- CONFIG ---------------- #
HF_API_TOKEN = st.secrets.get("HF_API_TOKEN", "")
HF_MODEL = "sshleifer/distilbart-cnn-12-6"

BASE_URL = "https://www.theguardian.com/football"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9"
}

IMAGE_DIR = "downloaded_images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# ---------------- HUGGING FACE ---------------- #
def summarize_hf(text):
    try:
        API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

        payload = {
            "inputs": text[:2000],
            "parameters": {"max_length": 80, "min_length": 30}
        }

        response = requests.post(API_URL, headers=headers, json=payload, timeout=20)

        if response.status_code != 200:
            return "⚠️ HF API Error"

        result = response.json()

        if isinstance(result, list):
            return result[0].get("summary_text", "No summary available")
        else:
            return "Summary unavailable"

    except Exception as e:
        return f"Error: {e}"

# ---------------- SCRAPER ---------------- #
def get_articles():
    try:
        res = requests.get(BASE_URL, headers=HEADERS, timeout=10)

        if res.status_code != 200:
            st.error("Failed to fetch homepage")
            return []

        soup = BeautifulSoup(res.text, "html.parser")

        articles = []
        links = soup.select("a[data-link-name='article']")

        seen = set()
        for link in links:
            url = link.get("href")
            title = link.get_text(strip=True)

            if url and url not in seen and title:
                seen.add(url)
                articles.append((title, url))

            if len(articles) == 5:
                break

        return articles

    except Exception as e:
        st.error(f"Error fetching articles: {e}")
        return []

# ---------------- FIXED ARTICLE SCRAPER ---------------- #
def scrape_article(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)

        if res.status_code != 200:
            return "", None

        soup = BeautifulSoup(res.text, "html.parser")

        text = ""

        # Multiple fallback selectors (IMPORTANT FIX)
        selectors = [
            "div[itemprop='articleBody'] p",
            "div[data-gu-name='body'] p",
            "div[data-gu-name='maincontent'] p",
            "main p"
        ]

        for selector in selectors:
            paragraphs = soup.select(selector)
            if paragraphs:
                text = " ".join(p.get_text() for p in paragraphs)
                break

        # Final fallback
        if not text:
            paragraphs = soup.find_all("p")
            text = " ".join(p.get_text() for p in paragraphs[:20])

        # Image extraction
        img_tag = soup.find("meta", property="og:image")
        image_url = img_tag["content"] if img_tag else None

        return text.strip(), image_url

    except Exception as e:
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
        return ["#Football", "#Soccer", "#News"]

# ---------------- IMAGE ---------------- #
def download_image(url, title):
    if not url:
        return None

    try:
        res = requests.get(url, headers=HEADERS, timeout=10)

        filename = re.sub(r'[\\/*?:"<>|]', "", title)[:50] + ".jpg"
        path = os.path.join(IMAGE_DIR, filename)

        with open(path, "wb") as f:
            f.write(res.content)

        return path

    except:
        return None

# ---------------- UI ---------------- #
st.set_page_config(page_title="⚽ Soccer News AI", layout="wide")

st.title("⚽ Soccer News AI Generator")
st.caption("Scrape → Summarize → Social Post")

if st.button("🚀 Fetch Latest News"):
    articles = get_articles()

    if not articles:
        st.warning("No articles found")
    else:
        for title, url in articles:
            st.divider()
            st.subheader(title)

            text, image_url = scrape_article(url)

            # Improved failure detection
            if not text or len(text) < 200:
                st.warning("⚠️ Article content too short or blocked")
                st.write(url)
                continue

            with st.spinner("🤖 Summarizing with AI..."):
                summary = summarize_hf(text)

            hashtags = generate_hashtags(text)
            image_path = download_image(image_url, title)

            # Display image
            if image_url:
                st.image(image_url, use_container_width=True)

            st.write(summary)

            post = f"""
🔥 {title}

📝 {summary}

🔗 {url}

{' '.join(hashtags)}
"""

            st.text_area("📋 Copy Post", post, height=150)
