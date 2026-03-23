import streamlit as st
import requests
import feedparser
import hashlib
import time
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
st.set_page_config(page_title="NEO-SCOUT CLEAN", layout="wide")

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ────────────────────────────────────────────────
# SOURCES (20)
# ────────────────────────────────────────────────
ALL_SOURCES = [
    ("GOAL", "https://www.goal.com/en/feeds/news"),
    ("BBC", "https://feeds.bbci.co.uk/sport/football/rss.xml"),
    ("GUARDIAN", "https://www.theguardian.com/football/rss"),
    ("ESPN", "https://www.espn.com/espn/rss/soccer/news"),
    ("SKY", "https://www.skysports.com/rss/12040"),
    ("90MIN", "https://www.90min.com/posts.rss"),
    ("CBS", "https://www.cbssports.com/rss/headlines/soccer/"),
    ("NBC", "https://www.nbcsports.com/soccer/rss.xml"),
    ("YAHOO", "https://sports.yahoo.com/soccer/rss/"),
    ("FOX", "https://api.foxsports.com/v1/rss?category=soccer"),
    ("REUTERS", "https://www.reutersagency.com/feed/?best-topics=sports"),
    ("AP", "https://apnews.com/hub/soccer"),
    ("MIRROR", "https://www.mirror.co.uk/sport/football/rss.xml"),
    ("INDEPENDENT", "https://www.independent.co.uk/sport/football/rss"),
    ("STANDARD", "https://www.standard.co.uk/sport/football/rss"),
    ("TALKSport", "https://talksport.com/football/feed/"),
    ("GIVEMESPORT", "https://www.givemesport.com/feed/"),
    ("FOOTBALL365", "https://www.football365.com/rss"),
    ("BLEACHER", "https://bleacherreport.com/articles.rss"),
    ("ATHLETIC", "https://theathletic.com/rss/football/")
]

if "source_limit" not in st.session_state:
    st.session_state.source_limit = 5

# ────────────────────────────────────────────────
# IMAGE FROM WEB (HEADLINE BASED)
# ────────────────────────────────────────────────
def fetch_image(query):
    try:
        return f"https://source.unsplash.com/900x400/?soccer,{query.replace(' ', ',')}"
    except:
        return None

# ────────────────────────────────────────────────
# SCRAPER
# ────────────────────────────────────────────────
def scrape(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        text = " ".join(p.get_text() for p in soup.find_all("p")[:30])
        return text
    except:
        return None

# ────────────────────────────────────────────────
# SUMMARIZER (SAFE)
# ────────────────────────────────────────────────
def summarize(text):
    try:
        sentences = text.split(". ")
        return ". ".join(sentences[:2]) + "."
    except:
        return "Summary unavailable."

# ────────────────────────────────────────────────
# FEED ENGINE (2H + UNIQUE)
# ────────────────────────────────────────────────
def parse_time(entry):
    try:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    except:
        return None

def get_feed(limit):
    items = []
    seen = set()

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=2)

    for name, url in ALL_SOURCES[:limit]:
        try:
            feed = feedparser.parse(url)

            for e in feed.entries:
                link = e.link
                title = e.title.upper()

                if link in seen:
                    continue

                t = parse_time(e)
                if not t or t < cutoff:
                    continue

                items.append({
                    "title": title,
                    "link": link,
                    "source": name,
                    "time": t.strftime("%H:%M")
                })

                seen.add(link)
                break
        except:
            continue

    return items

# ────────────────────────────────────────────────
# UI
# ────────────────────────────────────────────────
st.title("⚡ NEO-SCOUT CLEAN")

feed = get_feed(st.session_state.source_limit)

search = st.text_input("📡 FILTER").upper()
if search:
    feed = [f for f in feed if search in f["title"]]

for entry in feed:
    st.markdown("---")

    st.subheader(entry["title"])
    st.caption(f"{entry['source']} • {entry['time']}")

    # 🖼 IMAGE FROM WEB
    image = fetch_image(entry["title"])
    if image:
        st.image(image, use_container_width=True)

    # 🔗 LINK
    st.markdown(f"[Read full article]({entry['link']})")

    # 📦 SUMMARY UNDER LINK (YOUR REQUEST)
    text = scrape(entry["link"])
    if text:
        summary = summarize(text)

        st.markdown("### 🧠 Summary")
        st.info(summary)

# EXPAND SOURCES
if st.session_state.source_limit < 20:
    st.session_state.source_limit += 1
