import streamlit as st
import requests
import feedparser
import hashlib
import time
from duckduckgo_search import DDGS

# ────────────────────────────────────────────────
#               CYBERPUNK UI CONFIG
# ────────────────────────────────────────────────
st.set_page_config(page_title="NEO-SCOUT • v8.8", page_icon="⚽️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Roboto+Mono:wght@400;500&display=swap');
.stApp { background: linear-gradient(135deg, #0d0015, #16002b); color: #e0e0ff; }
h1, h2 { font-family: 'Orbitron', sans-serif; background: linear-gradient(90deg, #00f0ff, #c300ff); 
         -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.stButton > button { border: 2px solid #00f0ff; color: #00f0ff; background: transparent; border-radius: 12px; font-weight: 600; width: 100%; }
.stButton > button:hover { background: linear-gradient(45deg, #00f0ff, #c300ff); color: #000; box-shadow: 0 0 20px #00f0ff; }
.card { background: rgba(25,10,50,0.85); backdrop-filter: blur(15px); border: 1px solid #00f0ff22; 
        border-radius: 18px; padding: 1.5rem; margin-bottom: 1.5rem; transition: 0.3s; }
.card:hover { border-color: #c300ff; }
.source-tag { background: #00f0ff22; color: #00f0ff; padding: 3px 10px; border-radius: 6px; font-size: 0.75rem; border: 1px solid #00f0ff44; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#               NEURAL ENGINE v8.8
# ────────────────────────────────────────────────

@st.cache_data(ttl=1800)
def firecrawl_scrape(url):
    """Reliable Firecrawl extraction."""
    if "FIRECRAWL_KEY" not in st.secrets: return None, None
    headers = {"Authorization": f"Bearer {st.secrets['FIRECRAWL_KEY']}", "Content-Type": "application/json"}
    payload = {"url": url, "formats": ["markdown"], "onlyMainContent": True}
    try:
        r = requests.post("https://api.firecrawl.dev/v1/scrape", json=payload, headers=headers, timeout=25)
        if r.ok:
            data = r.json().get("data", {})
            return data.get("markdown", ""), data.get("metadata", {}).get("og:image")
    except: pass
    return None, None

def bart_dual_sentence(text, title):
    """Generates exactly two high-detail sentences for Facebook."""
    if not text or len(text) < 150: return "⚠️ Error: Article data stream too thin."
    
    api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    
    # Payload tuned for 2-sentence density
    payload = {
        "inputs": text[:4000],
        "parameters": {
            "max_length": 90,   # Shorter max to force 2 sentences
            "min_length": 55,   # Minimum length to ensure detail
            "do_sample": False,
            "repetition_penalty": 2.5
        },
        "options": {"wait_for_model": True}
    }
    
    try:
        r = requests.post(api_url, headers=headers, json=payload)
        res = r.json()
        
        if isinstance(res, list) and 'summary_text' in res[0]:
            raw_summary = res[0]['summary_text'].replace(' .', '.').strip()
            # Construct the final Facebook post
            fb_post = f"🚨 SOCCER UPDATE: {title}\n\n{raw_summary}\n\n⚽ #SoccerNews #FootballUpdate #BreakingNews #MatchDay"
            return fb_post
        return "❌ Neural Core Busy. Try again in 10s."
    except:
        return "🛠️ Connection to Neural Core Lost."

# ────────────────────────────────────────────────
#               EXPANDED SOURCE ENGINE
# ────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_mega_feed():
    """Increased sources to 8 major outlets."""
    sources = [
        ("GOAL", "https://www.goal.com/en/feeds/news"),
        ("SKY", "https://www.skysports.com/rss/12040"),
        ("BBC", "https://feeds.bbci.co.uk/sport/football/rss.xml"),
        ("GUARDIAN", "https://www.theguardian.com/football/rss"),
        ("ESPN", "https://www.espn.com/espn/rss/soccer/news"),
        ("90MIN", "https://www.90min.com/posts.rss"),
        ("TEAMTALK", "https://www.teamtalk.com/feed"),
        ("FOOTBALL365", "https://www.football365.com/feed")
    ]
    items = []
    seen = set()
    for name, url in sources:
        try:
            f = feedparser.parse(url)
            for e in f.entries:
                if e.link in seen or not any(k in e.title.lower() for k in ["football","soccer","goal","transfer"]):
                    continue
                seen.add(e.link)
                items.append({"title": e.title.upper(), "link": e.link, "source": name, "id": hashlib.md5(e.link.encode()).hexdigest()})
        except: pass
    return items[:40]

# ────────────────────────────────────────────────
#               MAIN INTERFACE
# ────────────────────────────────────────────────
st.title("⚡️ NEO-SCOUT • v8.8")
st.caption("MEGA-SOURCE FEED // DUAL-SENTENCE NEURAL SUMMARY")

feed = get_mega_feed()

# Filter/Search Bar
search = st.text_input("📡 SEARCH GLOBAL INTEL...", "").upper()
if search:
    feed = [f for f in feed if search in f['title']]

for entry in feed:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        c_title, c_btn = st.columns([4, 1])
        
        with c_title:
            st.markdown(f"**{entry['title']}**")
            st.markdown(f"<span class='source-tag'>{entry['source']}</span>", unsafe_allow_html=True)
        
        with c_btn:
            if st.button("🚀 SCAN", key=entry["id"]):
                with st.spinner("⚡️ Scraping..."):
                    content, thumb = firecrawl_scrape(entry["link"])
                
                if content:
                    with st.spinner("🧠 Synthesizing Dual-Sentence Intel..."):
                        fb_post = bart_dual_sentence(content, entry["title"])
                    
                    res1, res2 = st.columns([1, 2])
                    with res1:
                        if thumb: st.image(thumb, use_container_width=True)
                    with res2:
                        st.markdown("### 📱 FB COPY-READY")
                        st.code(fb_post, language="text")
                else:
                    st.error("🚫 Connection blocked by source site.")
        
        st.markdown('</div>', unsafe_allow_html=True)
