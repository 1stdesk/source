import streamlit as st
import requests
from bs4 import BeautifulSoup
import os
import re
from collections import Counter
import nltk

nltk.download('punkt')
nltk.download('stopwords')

# ---------------- CONFIG ---------------- #
HF_API_TOKEN = st.secrets.get("HF_API_TOKEN", "")  # store in Streamlit secrets
HF_MODEL = "facebook/bart-large-cnn"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

BASE_URL = "https://www.theguardian.com/football"
IMAGE_DIR = "downloaded_images"
os.makedirs(IMAGE_DIR, exist_ok=True)

# ---------------- HUGGING FACE ---------------- #
def summarize_hf(text):
    try:
        API_URL = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}

        payload = {
            "inputs": text[:2000],  # limit size
            "parameters": {
                "max_length": 80,
                "min_length": 30
            }
        }

        response = requests.post(API_URL, headers=headers, json=payload)
        result = response.json()

        if isinstance(result, list):
            return result[0]["summary_text"]
        else:
            return "Summary unavailable."

    except Exception as e:
        return f"Error: {e}"

# ---------------- SCRAPER ---------------- #
def get_articles():
    res = requests.get(BASE_URL, headers=HEADERS)
    soup = BeautifulSoup(res.text, "html.parser")

    articles = []
    links = soup.select("a[data-link-name='article']")[:10]

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

def scrape_article(url):
    try:
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")

        paragraphs = soup.select("div[itemprop='articleBody'] p")
        text = " ".join(p.get_text() for p in paragraphs)

        img_tag = soup.find("meta", property="og:image")
        image_url = img_tag["content"] if img_tag else None

        return text, image_url

    except:
        return "", None

# ---------------- HASHTAGS ---------------- #
def generate_hashtags(text):
    words = re.findall(r"\b[A-Za-z]{4,}\b", text.lower())
    stopwords = set(nltk.corpus.stopwords.words("english"))

    filtered = [w for w in words if w not in stopwords]
    common = Counter(filtered).most_common(5)

    return [f"#{w.capitalize()}" for w, _ in common]

# ---------------- IMAGE ---------------- #
def download_image(url, title):
    if not url:
        return None

    try:
        res = requests.get(url)
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
st.write("Scrape → Summarize → Social Post")

if st.button("🚀 Fetch Latest News"):
    articles = get_articles()

    for title, url in articles:
        st.divider()
        st.subheader(title)

        text, image_url = scrape_article(url)

        if not text:
            st.warning("Failed to fetch article")
            continue

        with st.spinner("Summarizing with AI..."):
            summary = summarize_hf(text)

        hashtags = generate_hashtags(text)
        image_path = download_image(image_url, title)

        # Display
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
