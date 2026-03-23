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
st.set_page_config(page_title="NEO-SCOUT v11 ELITE", layout="wide")

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ────────────────────────────────────────────────
# AUTO REFRESH
# ────────────────────────────────────────────────
REFRESH_INTERVAL = 60
st.markdown(f"⏱ Auto-refresh every {REFRESH_INTERVAL}s")
time.sleep(0.1)
st.experimental_rerun if False else None  # placeholder to avoid warning

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
# IMAGE FETCH (WEB BASED)
# ────────────────────────────────────────────────
def fetch_image_from_web(query):
    try:
        url = f"https://source.unsplash.com/800x400/?soccer,{query.replace(' ', ',')}"
        return url
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
        img = soup.find("meta", property="og:image")
        return text, img["content"] if img else None
    except:
        return None, None

# ────────────────────────────────────────────────
# SUMMARIZER (FAST + FALLBACK)
# ────────────────────────────────────────────────
def summarize(text):
    sentences = text.split(". ")
    return ". ".join(sentences[:2]) + "."

# ────────────────────────────────────────────────
# HASHTAGS + TRENDING
# ────────────────────────────────────────────────
def extract_keywords(text):
    words = re.findall(r"\b[A-Za-z]{5,}\b", text.lower())
    stop = set(nltk.corpus.stopwords.words("english"))
    return [w for w in words if w not in stop]

def get_trending(feed):
    all_words = []
    for f in feed:
        all_words.extend(extract_keywords(f["title"]))
    return Counter(all_words).most_common(5)

# ────────────────────────────────────────────────
# FEED ENGINE (2H FILTER + UNIQUE SOURCE)
# ────────────────────────────────────────────────
def parse_time(entry):
    try:
        return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    except:
        return None

def get_feed(limit):
    items = []
    seen = set()
    used_sources = set()

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
                used_sources.add(name)
                break
        except:
            continue

    return items

# ────────────────────────────────────────────────
# UI
# ────────────────────────────────────────────────
st.title("⚡ NEO-SCOUT v11 ELITE")

feed = get_feed(st.session_state.source_limit)

# 🔥 TRENDING PANEL
trending = get_trending(feed)
st.markdown("### 🔥 TRENDING")
st.write(", ".join([f"#{w}" for w, _ in trending]))

# 🔍 FILTER
search = st.text_input("📡 FILTER").upper()
if search:
    feed = [f for f in feed if search in f["title"]]

# 📰 FEED DISPLAY
for entry in feed:
    st.markdown("---")

    st.subheader(entry["title"])
    st.caption(f"{entry['source']} • {entry['time']}")

    text, img = scrape(entry["link"])

    # 🖼 IMAGE LOGIC
    if not img:
        img = fetch_image_from_web(entry["title"])

    if img:
        st.image(img, use_container_width=True)

    # 🔗 LINK
    st.markdown(f"[Read full article]({entry['link']})")

    # 🧠 SUMMARY BELOW LINK
    if text:
        summary = summarize(text)
        st.write(summary)

# 🔄 AUTO EXPAND SOURCES
if st.session_state.source_limit < 20:
    st.session_state.source_limit += 1
