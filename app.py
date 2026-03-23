import streamlit as st
import requests
import feedparser
import hashlib
import time
import re
from collections import Counter
from bs4 import BeautifulSoup
import nltk

nltk.download('punkt')
nltk.download('stopwords')

# ────────────────────────────────────────────────
#               CYBERPUNK UI CONFIG
# ────────────────────────────────────────────────
st.set_page_config(page_title="NEO-SCOUT • v10 PRO", page_icon="⚽️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Roboto+Mono:wght@400;500&display=swap');
.stApp { background: linear-gradient(135deg, #0d0015, #120022); color: #e0e0ff; }
h1, h2 { font-family: 'Orbitron', sans-serif; background: linear-gradient(90deg, #00f0ff, #c300ff); 
         -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.stButton > button { border: 2px solid #00f0ff; color: #00f0ff; background: transparent; border-radius: 12px; font-weight: 600; width: 100%; }
.card { background: rgba(30,10,60,0.8); backdrop-filter: blur(20px); border-radius: 20px; padding: 1.5rem; margin-bottom: 1rem; }
.source-tag { background: #c300ff22; padding: 4px 10px; border-radius: 6px; font-size: 0.7rem; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#               20 RSS SOURCES
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
    ("AP", "https://apnews.com/hub/soccer?utm_source=rss"),
    ("MIRROR", "https://www.mirror.co.uk/sport/football/rss.xml"),
    ("INDEPENDENT", "https://www.independent.co.uk/sport/football/rss"),
    ("STANDARD", "https://www.standard.co.uk/sport/football/rss"),
    ("TALKSport", "https://talksport.com/football/feed/"),
    ("GIVEMESPORT", "https://www.givemesport.com/feed/"),
    ("FOOTBALL365", "https://www.football365.com/rss"),
    ("BLEACHER", "https://bleacherreport.com/articles.rss"),
    ("THE ATHLETIC", "https://theathletic.com/rss/football/")
]

if "source_limit" not in st.session_state:
    st.session_state.source_limit = 3

# ────────────────────────────────────────────────
#               SCRAPER (FALLBACK SYSTEM)
# ────────────────────────────────────────────────
def basic_scrape(url):
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        text = " ".join(p.get_text() for p in soup.find_all("p")[:30])
        img = soup.find("meta", property="og:image")
        return text, img["content"] if img else None
    except:
        return None, None

@st.cache_data(ttl=1800)
def firecrawl_scrape(url):
    if "FIRECRAWL_KEY" not in st.secrets:
        return basic_scrape(url)

    try:
        headers = {"Authorization": f"Bearer {st.secrets['FIRECRAWL_KEY']}"}
        r = requests.post("https://api.firecrawl.dev/v1/scrape",
                          json={"url": url, "formats": ["markdown"], "onlyMainContent": True},
                          headers=headers, timeout=25)
        if r.ok:
            data = r.json()["data"]
            return data.get("markdown"), data.get("metadata", {}).get("og:image")
    except:
        pass

    return basic_scrape(url)

# ────────────────────────────────────────────────
#               AI SUMMARIZER (ROBUST)
# ────────────────────────────────────────────────
def summarize(text, title):
    api = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}

    for _ in range(5):
        try:
            r = requests.post(api, headers=headers,
                              json={"inputs": text[:4000], "options": {"wait_for_model": True}},
                              timeout=60)
            if r.status_code == 200:
                summary = r.json()[0]["summary_text"]
                tags = generate_tags(text)
                return f"🚨 {title}\n\n{summary}\n\n{' '.join(tags)}"
            elif r.status_code == 503:
                time.sleep(10)
        except:
            time.sleep(3)

    return "❌ AI overloaded"

# ────────────────────────────────────────────────
#               HASHTAGS (SMART)
# ────────────────────────────────────────────────
def generate_tags(text):
    words = re.findall(r"\b[A-Za-z]{5,}\b", text.lower())
    stop = set(nltk.corpus.stopwords.words("english"))
    common = Counter([w for w in words if w not in stop]).most_common(5)
    return [f"#{w.capitalize()}" for w, _ in common]

# ────────────────────────────────────────────────
#               FEED ENGINE
# ────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_feed(limit):
    items, seen = [], set()
    for name, url in ALL_SOURCES[:limit]:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries:
                if e.link not in seen:
                    seen.add(e.link)
                    items.append({
                        "title": e.title.upper(),
                        "link": e.link,
                        "source": name,
                        "id": hashlib.md5(e.link.encode()).hexdigest()
                    })
        except:
            pass
    return items[:40]

# ────────────────────────────────────────────────
#               UI
# ────────────────────────────────────────────────
st.title("⚡️ NEO-SCOUT v10 PRO")
st.caption(f"ACTIVE SOURCES: {st.session_state.source_limit}/20")

feed = get_feed(st.session_state.source_limit)

search = st.text_input("📡 FILTER INTEL").upper()
if search:
    feed = [f for f in feed if search in f["title"]]

for entry in feed:
    st.markdown('<div class="card">', unsafe_allow_html=True)

    col1, col2 = st.columns([4,1])
    with col1:
        st.markdown(f"**{entry['title']}**")
        st.markdown(f"<span class='source-tag'>{entry['source']}</span>", unsafe_allow_html=True)
    with col2:
        if st.button("🚀 SCAN", key=entry["id"]):
            content, img = firecrawl_scrape(entry["link"])

            if content:
                post = summarize(content, entry["title"])

                c1, c2 = st.columns([1,2])
                with c1:
                    if img:
                        st.image(img, use_container_width=True)
                with c2:
                    st.code(post)
            else:
                st.error("Blocked content")

    st.markdown('</div>', unsafe_allow_html=True)

# 🔥 AUTO INCREASE SOURCES EACH REFRESH
if st.session_state.source_limit < 20:
    st.session_state.source_limit += 1
