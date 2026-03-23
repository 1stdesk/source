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
# 🔥 NLTK FIX (STREAMLIT SAFE)
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
# ⚙ CONFIG
# ────────────────────────────────────────────────
st.set_page_config(page_title="NEO-SCOUT v12", layout="wide")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# ────────────────────────────────────────────────
# 🌍 SOURCES (20)
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
    st.session_state.source_limit = 6

# ────────────────────────────────────────────────
# 🖼 IMAGE SYSTEM (FIXED)
# ────────────────────────────────────────────────
def fetch_article_image(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(r.text, "html.parser")

        img = soup.find("meta", property="og:image")
        if img and img.get("content"):
            return img["content"]
    except:
        pass
    return None


def fetch_image(title, url):
    # 1. Try real article image
    img = fetch_article_image(url)
    if img:
        return img

    # 2. Stable fallback (no redirect issues)
    return "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?auto=format&fit=crop&w=1200&q=80"

# ────────────────────────────────────────────────
# 📰 SCRAPER
# ────────────────────────────────────────────────
def scrape(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text() for p in paragraphs[:30])
        return text
    except:
        return None

# ────────────────────────────────────────────────
# 🏷 HASHTAGS
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
# 🧠 SUMMARY (UNCHANGED)
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
# ⏱ FEED ENGINE
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

    for name, url in ALL_SOURCES[:limit]:
        try:
            feed = feedparser.parse(url)

            for e in feed.entries:
                link = e.link
                title = e.title.upper()

                if link in seen_links:
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
# 🎨 UI
# ────────────────────────────────────────────────
st.title("⚡ NEO-SCOUT v12")
st.caption("REAL-TIME SOCCER INTELLIGENCE • LAST 2 HOURS")

feed = get_feed(st.session_state.source_limit)

search = st.text_input("📡 FILTER NEWS").upper()
if search:
    feed = [f for f in feed if search in f["title"]]

for entry in feed:
    st.markdown("---")

    st.subheader(entry["title"])
    st.caption(f"{entry['source']} • {entry['time']} UTC")

    # 🖼 IMAGE (FIXED SYSTEM)
    img = fetch_image(entry["title"], entry["link"])
    st.image(img, use_container_width=True)

    # 🔗 LINK
    st.markdown(f"[Read full article]({entry['link']})")

    # 🧠 SUMMARY BOX
    text = scrape(entry["link"])
    if text:
        post = summarize(text, entry["title"])

        st.markdown("### 📋 Social Post")
        st.code(post)

# 🔄 EXPAND SOURCES GRADUALLY
if st.session_state.source_limit < 20:
    st.session_state.source_limit += 1
