import streamlit as st
import requests
import feedparser
import re
import os
from collections import Counter
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import nltk

# ────────────────────────────────────────────────
# NLTK FIX
# ────────────────────────────────────────────────
NLTK_DIR = "/tmp/nltk_data"
os.makedirs(NLTK_DIR, exist_ok=True)
nltk.data.path.append(NLTK_DIR)

try:
    nltk.download("punkt", download_dir=NLTK_DIR)
    nltk.download("stopwords", download_dir=NLTK_DIR)
except:
    pass

# ────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────
st.set_page_config(page_title="NEO-SCOUT v14", layout="wide")

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ────────────────────────────────────────────────
# 🌍 MASSIVE SOURCE LIST (YOUR LIST)
# ────────────────────────────────────────────────
ALL_SOURCES = [
    # (PASTE YOUR FULL LIST HERE EXACTLY — already supported)
]
# NOTE: your full list goes here (too large to repeat again)

# ────────────────────────────────────────────────
# SESSION STATE
# ────────────────────────────────────────────────
if "source_limit" not in st.session_state:
    st.session_state.source_limit = 10

if "page" not in st.session_state:
    st.session_state.page = 1

# ────────────────────────────────────────────────
# IMAGE SYSTEM
# ────────────────────────────────────────────────
def fetch_article_image(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        soup = BeautifulSoup(r.text, "html.parser")
        img = soup.find("meta", property="og:image")
        if img and img.get("content"):
            return img["content"]
    except:
        pass
    return None


def fetch_image(title, url):
    img = fetch_article_image(url)
    if img:
        return img
    return "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&w=1200&q=80"

# ────────────────────────────────────────────────
# SCRAPER
# ────────────────────────────────────────────────
def scrape(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(r.text, "html.parser")
        return " ".join(p.get_text() for p in soup.find_all("p")[:25])
    except:
        return None

# ────────────────────────────────────────────────
# HASHTAGS
# ────────────────────────────────────────────────
def generate_tags(text):
    try:
        words = re.findall(r"\b[A-Za-z]{5,}\b", text.lower())
        stop = set(nltk.corpus.stopwords.words("english"))
        common = Counter([w for w in words if w not in stop]).most_common(5)
        return [f"#{w.capitalize()}" for w, _ in common]
    except:
        return ["#Football", "#Soccer"]

# ────────────────────────────────────────────────
# SUMMARY (UNCHANGED)
# ────────────────────────────────────────────────
def summarize(text, title):
    try:
        sentences = text.split(". ")
        summary = ". ".join(sentences[:2]) + "."
    except:
        summary = "Summary unavailable."

    tags = generate_tags(text)

    return f"""🔥 {title}

📝 {summary}

{' '.join(tags)}"""

# ────────────────────────────────────────────────
# FEED ENGINE (OPTIMIZED)
# ────────────────────────────────────────────────
def parse_time(entry):
    try:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    except:
        return None


def get_feed(limit):
    items = []
    seen_links = set()

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=2)

    active_sources = ALL_SOURCES[:limit]

    for name, url in active_sources:
        try:
            feed = feedparser.parse(url)

            for e in feed.entries:
                link = getattr(e, "link", None)
                title = getattr(e, "title", "").upper()

                if not link or link in seen_links:
                    continue

                pub_time = parse_time(e)
                if not pub_time or pub_time < cutoff:
                    continue

                items.append({
                    "title": title,
                    "link": link,
                    "source": name,
                    "time": pub_time.strftime("%H:%M")
                })

                seen_links.add(link)
                break

        except:
            continue

    return items

# ────────────────────────────────────────────────
# UI
# ────────────────────────────────────────────────
st.title("⚡ NEO-SCOUT v14")
st.caption("GLOBAL SOCCER INTELLIGENCE • LAST 2 HOURS")

feed = get_feed(st.session_state.source_limit)

# FILTER
search = st.text_input("📡 FILTER NEWS").upper()
if search:
    feed = [f for f in feed if search in f["title"]]

# PAGINATION
ARTICLES_PER_PAGE = 5
end = st.session_state.page * ARTICLES_PER_PAGE
visible_feed = feed[:end]

# DISPLAY
for entry in visible_feed:
    st.markdown("---")

    st.subheader(entry["title"])
    st.caption(f"{entry['source']} • {entry['time']} UTC")

    img = fetch_image(entry["title"], entry["link"])
    st.image(img, use_container_width=True)

    st.markdown(f"[Read full article]({entry['link']})")

    text = scrape(entry["link"])
    if text:
        post = summarize(text, entry["title"])
        st.markdown("### 📋 Social Post")
        st.code(post)

# ────────────────────────────────────────────────
# CONTROLS (UPDATED)
# ────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    if st.button("📄 Load More Articles"):
        st.session_state.page += 1

with col2:
    if st.button("🌍 Load More Sources (+10)"):
        if st.session_state.source_limit < len(ALL_SOURCES):
            st.session_state.source_limit += 10
