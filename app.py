import streamlit as st
import requests
import feedparser
import hashlib
import time
import re
from collections import Counter
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import nltk

nltk.download('punkt')
nltk.download('stopwords')

# ────────────────────────────────────────────────
# UI CONFIG
# ────────────────────────────────────────────────
st.set_page_config(page_title="NEO-SCOUT v10.2", page_icon="⚽️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Roboto+Mono:wght@400;500&display=swap');
.stApp { background: linear-gradient(135deg, #0d0015, #120022); color: #e0e0ff; }
h1 { font-family: 'Orbitron', sans-serif; background: linear-gradient(90deg, #00f0ff, #c300ff); 
-webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.card { background: rgba(30,10,60,0.8); border-radius: 15px; padding: 1rem; margin-bottom: 1rem; }
.source-tag { background: #c300ff22; padding: 4px 10px; border-radius: 6px; font-size: 0.7rem; }
</style>
""", unsafe_allow_html=True)

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
    ("AP", "https://apnews.com/hub/soccer?utm_source=rss"),
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
# SCRAPER
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
        r = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            json={"url": url, "formats": ["markdown"], "onlyMainContent": True},
            headers=headers,
            timeout=25
        )
        if r.ok:
            data = r.json()["data"]
            return data.get("markdown"), data.get("metadata", {}).get("og:image")
    except:
        pass

    return basic_scrape(url)

# ────────────────────────────────────────────────
# SUMMARIZER (ROBUST)
# ────────────────────────────────────────────────
def local_summary(text):
    from sumy.parsers.plaintext import PlaintextParser
    from sumy.nlp.tokenizers import Tokenizer
    from sumy.summarizers.lsa import LsaSummarizer

    parser = PlaintextParser.from_string(text[:2000], Tokenizer("english"))
    summarizer = LsaSummarizer()
    return " ".join(str(s) for s in summarizer(parser.document, 2))


def summarize(text, title):
    HF_TOKEN = st.secrets.get("HF_TOKEN", "")
    models = [
        "sshleifer/distilbart-cnn-12-6",
        "facebook/bart-large-cnn"
    ]

    for model in models:
        api = f"https://api-inference.huggingface.co/models/{model}"
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}

        for _ in range(3):
            try:
                r = requests.post(
                    api,
                    headers=headers,
                    json={"inputs": text[:3000], "options": {"wait_for_model": True}},
                    timeout=45
                )

                if r.status_code == 200:
                    data = r.json()
                    if isinstance(data, list):
                        summary = data[0]["summary_text"]
                        return format_post(title, summary, text)

                elif r.status_code == 503:
                    time.sleep(5)
                elif r.status_code == 429:
                    time.sleep(5)

            except:
                time.sleep(2)

    # fallback
    summary = local_summary(text)
    return format_post(title, summary, text)

# ────────────────────────────────────────────────
# HASHTAGS
# ────────────────────────────────────────────────
def generate_tags(text):
    words = re.findall(r"\b[A-Za-z]{5,}\b", text.lower())
    stop = set(nltk.corpus.stopwords.words("english"))
    common = Counter([w for w in words if w not in stop]).most_common(5)
    return [f"#{w.capitalize()}" for w, _ in common]


def format_post(title, summary, text):
    tags = generate_tags(text)
    return f"""🚨 {title}

{summary}

{' '.join(tags)}"""

# ────────────────────────────────────────────────
# FEED ENGINE (KEY FEATURE)
# ────────────────────────────────────────────────
def parse_time(entry):
    try:
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    except:
        pass
    return None


@st.cache_data(ttl=120)
def get_feed(limit):
    items = []
    seen_links = set()
    used_sources = set()

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=2)

    for name, url in ALL_SOURCES[:limit]:

        if name in used_sources:
            continue

        try:
            feed = feedparser.parse(url)

            for entry in feed.entries:
                link = getattr(entry, "link", None)
                title = getattr(entry, "title", "").upper()

                if not link or link in seen_links:
                    continue

                pub_time = parse_time(entry)

                if not pub_time or pub_time < cutoff:
                    continue

                items.append({
                    "title": title,
                    "link": link,
                    "source": name,
                    "id": hashlib.md5(link.encode()).hexdigest(),
                    "time": pub_time.strftime("%H:%M UTC")
                })

                seen_links.add(link)
                used_sources.add(name)
                break

        except:
            continue

    return items

# ────────────────────────────────────────────────
# UI
# ────────────────────────────────────────────────
st.title("⚡ NEO-SCOUT v10.2")
st.caption(f"LIVE SOURCES: {st.session_state.source_limit}/20 • LAST 2 HOURS ONLY")

feed = get_feed(st.session_state.source_limit)

search = st.text_input("📡 FILTER").upper()
if search:
    feed = [f for f in feed if search in f["title"]]

for entry in feed:
    st.markdown('<div class="card">', unsafe_allow_html=True)

    col1, col2 = st.columns([4,1])
    with col1:
        st.markdown(f"**{entry['title']}**")
        st.markdown(
            f"<span class='source-tag'>{entry['source']} • {entry['time']}</span>",
            unsafe_allow_html=True
        )

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

# AUTO INCREASE SOURCES
if st.session_state.source_limit < 20:
    st.session_state.source_limit += 1
