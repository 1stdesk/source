import streamlit as st
import requests
import feedparser
import hashlib
from bs4 import BeautifulSoup
import time
import random

# --- CONFIG ---
st.set_page_config(page_title="NEO-SCOUT // V9", page_icon="📡", layout="wide")

# --- STYLING ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
.stApp { background-color: #050505; font-family: 'JetBrains Mono', monospace; }
h1, h2, h3, p, span, div { color: #00ff41 !important; text-shadow: 0 0 5px #00ff41; }
.stElementContainer div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #0a0a0a !important;
    border: 1px solid #00ff41 !important;
    box-shadow: 0 0 15px rgba(0,255,65,0.2);
    padding: 20px; border-radius: 4px; margin-bottom: 20px;
}
.status-tag { font-size: 0.7rem; padding: 2px 6px; border: 1px solid #00ff41; margin-bottom: 10px; display: inline-block; }
.char-counter { font-size: 0.8rem; color: #888 !important; text-align: right; }
</style>
""", unsafe_allow_html=True)

# --- SMART FALLBACK ---
def smart_fallback_summary(text):
    sentences = text.split('. ')
    if len(sentences) < 3:
        return text[:200]

    keywords = ["goal", "transfer", "win", "loss", "injury", "deal", "match"]
    scored = []

    for s in sentences:
        score = sum(1 for k in keywords if k in s.lower())
        score += len(s) / 100
        scored.append((score, s))

    top = sorted(scored, reverse=True)[:3]
    return ". ".join([s[1] for s in top]).strip() + "."

# --- FORMAT OUTPUT ---
def format_summary_output(summary, title):
    return f"""⚽ {title}

🔥 {summary}
"""

# --- AI ENGINE ---
def query_ai_deep(text, title=""):
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"

    if "HF_TOKEN" not in st.secrets:
        return format_summary_output(smart_fallback_summary(text), title)

    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}

    prompt = f"""
Summarize this football news article in a sharp, engaging way.

Rules:
- Max 3 sentences
- Sentence 1: Main breaking news
- Sentence 2: Key details
- Sentence 3: Context/impact
- Style: ESPN / BBC Sport

Title: {title}

Article:
{text[:1200]}
"""

    payload = {
        "inputs": prompt,
        "parameters": {"max_length": 140, "min_length": 60, "temperature": 0.7}
    }

    wait_times = [3, 6, 10]

    for wait in wait_times:
        try:
            r = requests.post(API_URL, headers=headers, json=payload, timeout=20)
            res = r.json()

            if isinstance(res, list):
                return format_summary_output(res[0]['summary_text'], title)

            if "estimated_time" in res:
                time.sleep(wait)
                continue

        except:
            continue

    return format_summary_output(smart_fallback_summary(text), title)

# --- CACHE ---
@st.cache_data(ttl=3600)
def cached_summary(text, title):
    return query_ai_deep(text, title)

# --- TAG ENGINE ---
def generate_viral_tags(title):
    base = ["#Football", "#SoccerNews", "#Breaking", "#Sports"]

    t = title.lower()
    if "transfer" in t:
        base += ["#TransferNews", "#HereWeGo"]
    if "goal" in t or "win" in t:
        base += ["#MatchDay", "#Highlights"]
    if "injury" in t:
        base += ["#InjuryUpdate"]

    return " ".join(random.sample(base, k=min(5, len(base))))

# --- BREAKING DETECTOR ---
def is_breaking_news(title):
    keywords = ["BREAKING", "CONFIRMED", "DONE DEAL"]
    return any(k in title.upper() for k in keywords)

# --- FETCH RSS ---
@st.cache_data(ttl=600)
def get_live_stream():
    feeds = [
        "https://www.goal.com/en/feeds/news",
        "https://www.skysports.com/rss/12040",
        "http://feeds.bbci.co.uk/sport/football/rss.xml"
    ]

    stream = []
    for url in feeds:
        f = feedparser.parse(url)
        for entry in f.entries[:6]:
            stream.append({
                "id": hashlib.md5(entry.link.encode()).hexdigest(),
                "title": entry.title.upper(),
                "link": entry.link,
                "src": url.split('/')[2].upper()
            })
    return stream

# --- SCRAPER ---
def scrape_intel(url):
    try:
        r = requests.get(url, timeout=6, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.content, 'html.parser')

        img = soup.find("meta", property="og:image")

        paras = [p.get_text().strip() for p in soup.find_all('p')]
        paras = [p for p in paras if len(p) > 60 and "cookie" not in p.lower()]

        return " ".join(paras[:6]), (img["content"] if img else None)

    except:
        return "", None

# --- UI ---
st.title("📡 NEO-SCOUT // V9.0 ELITE")

news_stream = get_live_stream()

for item in news_stream:
    with st.container(border=True):

        st.markdown(f'<div class="status-tag">NODE_{item["src"]}</div>', unsafe_allow_html=True)

        if is_breaking_news(item['title']):
            st.error("🚨 BREAKING NEWS")

        st.subheader(item['title'])

        if st.button("🔬 RUN INTEL", key=item['id']):

            with st.spinner(">> SCANNING DATA..."):
                raw_text, image = scrape_intel(item['link'])

                if image:
                    st.image(image, use_container_width=True)

                    # Download button
                    try:
                        img_data = requests.get(image).content
                        st.download_button("⬇ DOWNLOAD IMAGE", img_data, file_name="news.jpg")
                    except:
                        pass

                if len(raw_text) > 100:
                    summary = cached_summary(raw_text, item['title'])
                    tags = generate_viral_tags(item['title'])

                    full_post = f"{summary}\n\n{tags}"

                    st.text_area(">> SOCIAL READY", value=full_post, height=200)

                    # Copy button
                    st.code(full_post)

                    char_count = len(full_post)

                    st.markdown(
                        f'<div class="char-counter">CHARS: {char_count} | '
                        f'X: {"✅" if char_count <= 280 else "❌"} | TIKTOK: ✅</div>',
                        unsafe_allow_html=True
                    )

                else:
                    st.error(">> DATA TOO SHORT")

        st.markdown(f"[>> SOURCE LINK]({item['link']})")

st.markdown("---")
st.write(">> SYSTEM ONLINE // NEO-SCOUT V9")
