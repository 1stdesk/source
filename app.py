import streamlit as st
import requests
import feedparser
import hashlib
from bs4 import BeautifulSoup
import time
import random

# --- CONFIG ---
st.set_page_config(page_title="NEO-SCOUT // V12", page_icon="📡", layout="wide")

# --- UI: GOOGLE + GLASS STYLE ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background: linear-gradient(135deg, #eef2ff, #f8fafc);
}

.block-container {
    max-width: 820px;
    margin: auto;
    padding-top: 80px;
}

.glass {
    background: rgba(255,255,255,0.25);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border-radius: 20px;
    padding: 25px;
    border: 1px solid rgba(255,255,255,0.3);
    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
}

.news-card {
    background: rgba(255,255,255,0.55);
    backdrop-filter: blur(12px);
    border-radius: 18px;
    padding: 18px;
    margin-bottom: 18px;
    transition: all 0.2s ease;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}

.news-card:hover {
    transform: translateY(-5px);
}

div.stButton > button {
    border-radius: 999px;
    background: white;
    border: 1px solid #ddd;
    padding: 8px 18px;
    transition: 0.2s;
}

div.stButton > button:hover {
    background: #f1f3f4;
    box-shadow: 0 4px 10px rgba(0,0,0,0.15);
}

.google-title {
    text-align: center;
    font-size: 42px;
    font-weight: 600;
    margin-bottom: 20px;
}

.breaking {
    color: white;
    background: #ea4335;
    padding: 4px 10px;
    border-radius: 8px;
    font-size: 12px;
    display: inline-block;
    margin-bottom: 8px;
}
</style>
""", unsafe_allow_html=True)

# --- REFRESH ---
if "refresh_key" not in st.session_state:
    st.session_state.refresh_key = 0

if st.button("🔄 REFRESH"):
    st.session_state.refresh_key += 1
    st.cache_data.clear()
    st.rerun()

# --- CLEAN TEXT ---
def clean_text(text):
    lines = text.split("\n")
    cleaned, seen = [], set()

    for line in lines:
        line = line.strip()
        if len(line) < 40:
            continue
        if any(x in line.lower() for x in ["cookie", "subscribe", "sign up"]):
            continue
        if line not in seen:
            seen.add(line)
            cleaned.append(line)

    return " ".join(cleaned)

# --- CLEAN SUMMARY ---
def clean_summary(summary):
    sentences = summary.split(". ")
    unique, seen = [], set()

    for s in sentences:
        s = s.strip()
        if s and s not in seen:
            seen.add(s)
            unique.append(s)

    return ". ".join(unique[:3]).strip() + "."

# --- SIMILARITY ---
def is_similar(t1, t2):
    ignore = {"the","and","to","in","of","for","on","with"}
    s1 = set([w for w in t1.lower().split() if w not in ignore])
    s2 = set([w for w in t2.lower().split() if w not in ignore])
    return len(s1.intersection(s2)) >= 3

def find_related(main, all_items):
    return [i for i in all_items if i["id"] != main["id"] and is_similar(main["title"], i["title"])][:5]

# --- SCRAPER ---
def scrape_intel(url):
    try:
        r = requests.get(url, timeout=6, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.content, 'html.parser')

        img = soup.find("meta", property="og:image")
        paras = [p.get_text().strip() for p in soup.find_all('p')]
        paras = [p for p in paras if len(p) > 60]

        text = " ".join(paras[:6])
        text = clean_text(text)

        return text, (img["content"] if img else None)

    except:
        return "", None

# --- MERGE ---
def merge_articles(main, all_items):
    related = find_related(main, all_items)

    combined = ""
    main_text, img = scrape_intel(main["link"])
    combined += main_text

    for r in related:
        txt, _ = scrape_intel(r["link"])
        combined += "\n" + txt

    return combined, related, img

# --- FALLBACK ---
def smart_fallback(text):
    s = text.split(". ")
    return ". ".join(s[:3]) if len(s) >= 3 else text[:200]

# --- AI ---
def query_ai(text, title=""):
    if "HF_TOKEN" not in st.secrets:
        return clean_summary(smart_fallback(text))

    API = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}

    prompt = f"""
You are a professional football journalist.

Write a clean match report.

FORMAT:
1. Result + key player
2. How match was decided
3. Impact

RULES:
- Max 60 words
- No repetition
- Clear and sharp

Title: {title}

{text[:1200]}
"""

    try:
        r = requests.post(API, headers=headers, json={"inputs": prompt}, timeout=20)
        res = r.json()
        if isinstance(res, list):
            return clean_summary(res[0]["summary_text"])
    except:
        pass

    return clean_summary(smart_fallback(text))

@st.cache_data(ttl=3600)
def cached_summary(text, title):
    return query_ai(text, title)

# --- TAGS ---
def generate_tags(title):
    base = ["#Football", "#SoccerNews", "#Breaking"]
    if "transfer" in title.lower():
        base += ["#TransferNews"]
    return " ".join(random.sample(base, k=min(4, len(base))))

# --- BREAKING ---
def is_breaking(title):
    return any(k in title for k in ["BREAKING", "CONFIRMED"])

# --- FEEDS ---
@st.cache_data(ttl=600)
def get_news(key):
    feeds = [
        "https://www.goal.com/en/feeds/news",
        "https://www.skysports.com/rss/12040",
        "http://feeds.bbci.co.uk/sport/football/rss.xml",
        "https://www.espn.com/espn/rss/soccer/news",
        "https://www.theguardian.com/football/rss",
        "https://talksport.com/football/feed/",
        "https://www.90min.com/rss",
        "https://www.fourfourtwo.com/rss",
        "https://www.cbssports.com/rss/headlines/soccer/",
        "https://www.foxsports.com/soccer/rss",
        "https://www.mirror.co.uk/sport/football/rss.xml",
        "https://metro.co.uk/sport/football/feed/",
        "https://www.independent.co.uk/sport/football/rss",
        "https://www.sportingnews.com/uk/rss",
        "https://www.worldsoccertalk.com/feed/",
        "https://www.mlssoccer.com/rss",
        "https://www.laliga.com/rss",
        "https://www.premierleague.com/news/rss.xml",
        "https://www.bundesliga.com/rss/news",
        "https://www.besoccer.com/rss/news"
    ]

    out = []
    for url in feeds:
        f = feedparser.parse(url)
        for e in f.entries[:3]:
            out.append({
                "id": hashlib.md5(e.link.encode()).hexdigest(),
                "title": e.title.upper(),
                "link": e.link,
                "src": url.split('/')[2]
            })
    return out

# --- HEADER ---
st.markdown("""
<div class="google-title">
<span style='color:#4285F4'>N</span>
<span style='color:#EA4335'>E</span>
<span style='color:#FBBC05'>O</span>
<span style='color:#4285F4'>-</span>
<span style='color:#34A853'>S</span>
<span style='color:#EA4335'>C</span>
<span style='color:#4285F4'>O</span>
<span style='color:#FBBC05'>U</span>
<span style='color:#34A853'>T</span>
</div>
""", unsafe_allow_html=True)

# --- MAIN ---
st.markdown('<div class="glass">', unsafe_allow_html=True)

news = get_news(st.session_state.refresh_key)

for item in news:
    st.markdown('<div class="news-card">', unsafe_allow_html=True)

    st.caption(f"🌐 {item['src']}")

    if is_breaking(item["title"]):
        st.markdown('<div class="breaking">🚨 BREAKING</div>', unsafe_allow_html=True)

    st.subheader(item["title"])

    if st.button("🧠 MULTI-SOURCE INTEL", key=item["id"]):
        with st.spinner("AGGREGATING + CLEANING + ANALYZING..."):

            merged_text, related, img = merge_articles(item, news)

            if img:
                st.image(img)
                try:
                    st.download_button("DOWNLOAD IMAGE", requests.get(img).content)
                except:
                    pass

            summary = cached_summary(merged_text, item["title"])
            tags = generate_tags(item["title"])

            st.success(f"SOURCES USED: {1 + len(related)}")

            for r in related:
                st.caption(f"↳ {r['src']}")

            full = f"⚽ {item['title']}\n\n{summary}\n\n{tags}"

            st.text_area("OUTPUT", full, height=200)
            st.code(full)

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

st.markdown("---")
st.write("SYSTEM ACTIVE // V12 PRO")
