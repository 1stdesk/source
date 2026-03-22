import streamlit as st
import requests
import feedparser
import hashlib
from bs4 import BeautifulSoup
from collections import Counter
import random

# --- CONFIG ---
st.set_page_config(page_title="NEO-SCOUT V15", page_icon="📡", layout="wide")

# --- SESSION ---
if "refresh_key" not in st.session_state:
    st.session_state.refresh_key = 0

# --- SIDEBAR ---
with st.sidebar:
    st.title("📡 NEO-SCOUT V15")

    if st.button("🔄 Refresh Feed"):
        st.session_state.refresh_key += 1
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")

    auto_ai = st.checkbox("🧠 Auto AI", value=False)
    show_images = st.checkbox("🖼 Images", value=True)

# --- UTIL ---
def clean_text(text):
    return " ".join([l.strip() for l in text.split("\n") if len(l) > 40])

def clean_summary(text):
    s = text.split(". ")
    return ". ".join(s[:3]) + "."

def keywords(title):
    ignore = {"THE","AND","TO","IN","OF","FOR","WITH"}
    return [w for w in title.split() if w not in ignore]

# --- SCRAPER (CACHED PER URL) ---
@st.cache_data(ttl=1800)
def scrape(url):
    try:
        r = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.content, 'html.parser')

        img = soup.find("meta", property="og:image")

        paras = [p.get_text() for p in soup.find_all("p")]
        text = clean_text(" ".join(paras[:6]))

        return text, (img["content"] if img else None)
    except:
        return "", None

# --- AI ---
def ai_summary(text):
    if "HF_TOKEN" not in st.secrets:
        return clean_summary(text)

    try:
        API = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
        headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}

        r = requests.post(API, headers=headers, json={"inputs": text[:1000]}, timeout=10)
        out = r.json()

        if isinstance(out, list):
            return clean_summary(out[0]["summary_text"])
    except:
        pass

    return clean_summary(text)

# --- FEEDS ---
@st.cache_data(ttl=600)
def get_news(key):
    feeds = [
        "https://www.goal.com/en/feeds/news",
        "https://www.skysports.com/rss/12040",
        "http://feeds.bbci.co.uk/sport/football/rss.xml",
        "https://www.espn.com/espn/rss/soccer/news",
        "https://www.theguardian.com/football/rss",
    ]

    seen = set()
    items = []

    for f in feeds:
        feed = feedparser.parse(f)
        for e in feed.entries[:4]:

            title = e.title.upper()

            if title in seen:
                continue
            seen.add(title)

            items.append({
                "id": hashlib.md5(e.link.encode()).hexdigest(),
                "title": title,
                "link": e.link,
                "src": f.split('/')[2]
            })

    return items

# --- GROUP SIMILAR ---
def group_news(news):
    groups = []
    used = set()

    for item in news:
        if item["id"] in used:
            continue

        group = [item]
        used.add(item["id"])

        for other in news:
            if other["id"] not in used:
                if len(set(keywords(item["title"])) & set(keywords(other["title"]))) >= 3:
                    group.append(other)
                    used.add(other["id"])

        groups.append(group)

    return groups

# --- TRENDING ---
def get_trends(news):
    words = []
    for n in news:
        words += keywords(n["title"])
    return Counter(words).most_common(10)

# --- HEADER ---
st.title("📡 NEO-SCOUT V15")
st.caption("Live Football Intelligence Feed")

news = get_news(st.session_state.refresh_key)
groups = group_news(news)

col_main, col_side = st.columns([3,1])

# --- MAIN FEED ---
with col_main:

    for group in groups:

        main = group[0]

        st.markdown("### " + main["title"])
        st.caption(main["src"])

        cols = st.columns([1,1,1])

        with cols[0]:
            if st.button("🧠 Analyze", key=main["id"]):

                text, img = scrape(main["link"])

                if img and show_images:
                    st.image(img)

                summary = ai_summary(text)
                st.write(summary)

        with cols[1]:
            st.markdown(f"[🔗 Open Article]({main['link']})")

        with cols[2]:
            tags = keywords(main["title"])[:3]
            st.caption(" ".join([f"#{t}" for t in tags]))

        if len(group) > 1:
            with st.expander(f"Related ({len(group)-1})"):
                for g in group[1:]:
                    st.write(g["title"])

        st.markdown("---")

# --- SIDE ---
with col_side:
    st.subheader("🔥 Trending")

    for word, count in get_trends(news):
        st.write(f"{word} ({count})")

st.markdown("---")
st.write("SYSTEM ACTIVE // V15 FEED ENGINE")
