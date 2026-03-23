import streamlit as st
import requests
import feedparser
import hashlib
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
st.set_page_config(page_title="NEO-SCOUT FINAL", layout="wide")

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ────────────────────────────────────────────────
# SOURCES
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
# IMAGE FETCH (FIXED)
# ────────────────────────────────────────────────
def fetch_image(query):
    try:
        url = f"https://source.unsplash.com/featured/?soccer,{query}"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.url  # important (redirect final URL)
    except:
        pass

    # fallback image
    return "https://images.unsplash.com/photo-1508098682722-e99c43a406b2"

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
# HASHTAGS
# ────────────────────────────────────────────────
def generate_tags(text):
    try:
        words = re.findall(r"\b[A-Za-z]{5,}\b", text.lower())
        stop = set(nltk.corpus.stopwords.words("english"))
        common = Counter([w for w in words if w not in stop]).most_common(5)
        return [f"#{w.capitalize()}" for w, _ in common]
    except:
        return ["#Football", "#Soccer", "#News"]

# ────────────────────────────────────────────────
# SUMMARY (FIXED FORMAT)
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
# FEED ENGINE
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
st.title("⚡ NEO-SCOUT FINAL")

feed = get_feed(st.session_state.source_limit)

search = st.text_input("📡 FILTER").upper()
if search:
    feed = [f for f in feed if search in f["title"]]

for entry in feed:
    st.markdown("---")

    st.subheader(entry["title"])
    st.caption(f"{entry['source']} • {entry['time']}")

    # 🖼 IMAGE FIXED
    img = fetch_image(entry["title"])
    st.image(img, use_container_width=True)

    # 🔗 LINK
    st.markdown(f"[Read full article]({entry['link']})")

    # 📦 SUMMARY WITH TITLE + HASHTAGS
    text = scrape(entry["link"])
    if text:
        post = summarize(text, entry["title"])

        st.markdown("### 📋 Social Post")
        st.code(post)

# EXPAND SOURCES
if st.session_state.source_limit < 20:
    st.session_state.source_limit += 1
