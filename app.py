import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import hashlib
import re

# ================= CONFIG =================
st.set_page_config(page_title="⚽ AI Football News", layout="wide")

MAX_ARTICLES = 2  # keep LOW for speed (BART is heavy)

SOURCES = [
    ("BBC", "https://feeds.bbci.co.uk/sport/football/rss.xml"),
    ("ESPN", "https://www.espn.com/espn/rss/soccer/news"),
]

# ================= LOAD MODEL =================
@st.cache_resource
def load_model():
    return pipeline("summarization", model="facebook/bart-large-cnn")

summarizer = load_model()

# ================= HELPERS =================
def clean_html(text):
    return re.sub('<.*?>', '', text)

def get_article_content(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")

        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text() for p in paragraphs])

        return text[:1500]  # keep SHORT for speed
    except:
        return None


def summarize_article(text):
    try:
        result = summarizer(
            text,
            max_length=100,
            min_length=30,
            do_sample=False
        )
        return result[0]["summary_text"]
    except:
        # fallback (instant)
        sentences = text.split(".")
        return ". ".join(sentences[:2]) + "."

# ================= FETCH =================
@st.cache_data(ttl=300)
def fetch_news():
    articles = []
    seen = set()

    for source_name, source_url in SOURCES:
        feed = feedparser.parse(source_url)

        for entry in feed.entries[:MAX_ARTICLES]:
            article_id = hashlib.md5(entry.link.encode()).hexdigest()

            if article_id in seen:
                continue

            content = get_article_content(entry.link)
            if not content:
                continue

            summary = summarize_article(content)

            image = None
            if "media_content" in entry:
                image = entry.media_content[0]["url"]

            articles.append({
                "title": entry.title,
                "summary": summary,
                "link": entry.link,
                "image": image,
                "source": source_name
            })

            seen.add(article_id)

    return articles

# ================= UI =================

st.markdown("""
<h1 style='text-align:center;'>⚽ AI Football News</h1>
<p style='text-align:center;color:gray;'>Powered by BART (Free AI)</p>
""", unsafe_allow_html=True)

with st.spinner("Loading news..."):
    news = fetch_news()

if not news:
    st.warning("No articles found.")

# TOP STORY
top = news[0]

st.markdown("## 🔥 Top Story")

if top["image"]:
    st.image(top["image"], use_container_width=True)

st.markdown(f"### {top['title']}")
st.write(top["summary"])
st.markdown(f"[Read more →]({top['link']})")

st.divider()

# GRID
st.markdown("## 📰 Latest News")

cols = st.columns(2)

for i, article in enumerate(news[1:]):
    with cols[i % 2]:
        if article["image"]:
            st.image(article["image"], use_container_width=True)

        st.markdown(f"**{article['title']}**")
        st.caption(article["source"])
        st.write(article["summary"])
        st.markdown(f"[Read more →]({article['link']})")
        st.markdown("---")
