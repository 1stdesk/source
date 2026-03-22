import streamlit as st
import requests
import feedparser
import hashlib
from bs4 import BeautifulSoup
import random
from collections import Counter

# --- CONFIG ---
st.set_page_config(page_title="NEO-SCOUT V14", page_icon="📡", layout="wide")

# --- SESSION ---
if "refresh_key" not in st.session_state:
    st.session_state.refresh_key = 0

# --- SIDEBAR ---
with st.sidebar:
    st.title("📡 NEO-SCOUT")

    if st.button("🔄 Refresh"):
        st.session_state.refresh_key += 1
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    st.subheader("Filters")

    show_breaking = st.checkbox("🚨 Breaking Only")
    auto_ai = st.checkbox("🧠 Auto AI", value=True)
    show_images = st.checkbox("🖼 Images", value=True)

# --- CLEAN TEXT ---
def clean_text(text):
    lines = text.split("\n")
    cleaned = []
    for l in lines:
        l = l.strip()
        if len(l) > 40 and "cookie" not in l.lower():
            cleaned.append(l)
    return " ".join(cleaned)

def clean_summary(text):
    s = text.split(". ")
    return ". ".join(s[:3]).strip() + "."

# --- SIMILARITY ---
def is_similar(a, b):
    s1 = set(a.lower().split())
    s2 = set(b.lower().split())
    return len(s1 & s2) >= 3

# --- SCRAPER ---
def scrape(url):
    try:
        r = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.content, 'html.parser')

        img = soup.find("meta", property="og:image")

        paras = [p.get_text() for p in soup.find_all("p")]
        text = clean_text(" ".join(paras[:5]))

        return text, (img["content"] if img else None)
    except:
        return "", None

# --- AI ---
def ai_summary(text, title):
    if "HF_TOKEN" not in st.secrets:
        return clean_summary(text)

    try:
        API = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
        headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}

        r = requests.post(API, headers=headers, json={"inputs": text[:1200]}, timeout=15)
        out = r.json()

        if isinstance(out, list):
            return clean_summary(out[0]["summary_text"])
    except:
        pass

    return clean_summary(text)

@st.cache_data(ttl=3600)
def cached_ai(text, title):
    return ai_summary(text, title)

# --- FEEDS ---
@st.cache_data(ttl=600)
def get_news(key):
    feeds = [
        "https://www.goal.com/en/feeds/news",
        "https://www.skysports.com/rss/12040",
        "http://feeds.bbci.co.uk/sport/football/rss.xml",
        "https://www.espn.com/espn/rss/soccer/news",
        "https://www.theguardian.com/football/rss"
    ]

    seen = set()
    data = []

    for f in feeds:
        feed = feedparser.parse(f)
        for e in feed.entries[:4]:
            title = e.title.upper()

            if title in seen:
                continue
            seen.add(title)

            data.append({
                "id": hashlib.md5(e.link.encode()).hexdigest(),
                "title": title,
                "link": e.link,
                "src": f.split('/')[2]
            })

    return data

# --- TRENDING ---
def get_trending(news):
    words = []
    ignore = {"THE","AND","TO","IN","OF","FOR"}
    for n in news:
        words += [w for w in n["title"].split() if w not in ignore]
    return Counter(words).most_common(8)

# --- BREAKING ---
def is_breaking(title):
    return "BREAKING" in title or "CONFIRMED" in title

# --- HEADER ---
st.title("📡 NEO-SCOUT V14")
st.caption("Elite Football Intelligence System")

# --- MAIN LAYOUT ---
news = get_news(st.session_state.refresh_key)

col_main, col_side = st.columns([3,1])

# --- MAIN FEED ---
with col_main:

    # Breaking banner
    breaking_news = [n for n in news if is_breaking(n["title"])]

    if breaking_news:
        st.error(f"🚨 BREAKING: {breaking_news[0]['title']}")

    for item in news:

        if show_breaking and not is_breaking(item["title"]):
            continue

        st.markdown("---")
        st.subheader(item["title"])
        st.caption(item["src"])

        with st.expander("📊 View Intelligence"):

            text, img = scrape(item["link"])

            if img and show_images:
                st.image(img)

            if auto_ai:
                summary = cached_ai(text, item["title"])
                st.write(summary)

# --- SIDE PANEL ---
with col_side:
    st.subheader("🔥 Trending")

    trends = get_trending(news)
    for t, c in trends:
        st.write(f"{t} ({c})")

st.markdown("---")
st.write("SYSTEM ACTIVE // V14 ELITE")
