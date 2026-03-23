import streamlit as st
import requests
import feedparser
import hashlib
from duckduckgo_search import DDGS

# ────────────────────────────────────────────────
#               CYBERPUNK UI CONFIG
# ────────────────────────────────────────────────
st.set_page_config(page_title="NEO-SCOUT • v8.6", page_icon="⚽️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Roboto+Mono:wght@400;500&display=swap');
.stApp { background: linear-gradient(135deg, #0d0015, #1a0033); color: #e0e0ff; }
h1, h2 { font-family: 'Orbitron', sans-serif; background: linear-gradient(90deg, #00f0ff, #c300ff); 
         -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.stButton > button { border: 2px solid #00f0ff; color: #00f0ff; background: transparent; border-radius: 12px; font-weight: 600; width: 100%; }
.stButton > button:hover { background: linear-gradient(45deg, #00f0ff, #c300ff); color: #000; box-shadow: 0 0 15px #00f0ff; }
.card { background: rgba(20,10,40,0.85); backdrop-filter: blur(12px); border: 1px solid #00f0ff33; 
        border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem; }
.intel-box { background: rgba(25,10,45,0.95); border-left: 5px solid #00f0ff; padding: 1.2rem; border-radius: 10px; color: #00f0ff; font-family: 'Roboto Mono', monospace; }
.fb-ready { background: #1877F222; border: 1px dashed #1877F2; padding: 15px; border-radius: 10px; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#               NEURAL & SCRAPE CORES
# ────────────────────────────────────────────────

@st.cache_data(ttl=1800)
def firecrawl_scrape(url):
    """Scrapes clean Markdown and Meta Image from Firecrawl."""
    if "FIRECRAWL_KEY" not in st.secrets:
        return "Missing FIRECRAWL_KEY", None
    headers = {"Authorization": f"Bearer {st.secrets['FIRECRAWL_KEY']}", "Content-Type": "application/json"}
    payload = {"url": url, "formats": ["markdown"], "onlyMainContent": True}
    try:
        r = requests.post("https://api.firecrawl.dev/v1/scrape", json=payload, headers=headers, timeout=20)
        if r.ok:
            data = r.json().get("data", {})
            img = data.get("metadata", {}).get("og:image")
            return data.get("markdown", ""), img
        return f"Scrape Failed: {r.status_code}", None
    except: return "Connection Error", None

@st.cache_data(ttl=1800)
def bart_fb_summary(text, title):
    """Summarizes text via BART and appends Facebook formatting/hashtags."""
    if not text or len(text) < 100: return "Data stream too weak for analysis."
    
    api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    payload = {"inputs": text[:3000], "parameters": {"max_length": 130, "min_length": 60}}
    
    try:
        r = requests.post(api_url, headers=headers, json=payload)
        summary = r.json()[0]['summary_text'] if r.ok else "Neural Core Timeout."
        
        # Post-Processing: Create the Facebook-ready block
        fb_post = f"🚨 SOCCER UPDATE: {title}\n\n{summary}\n\n⚽ #SoccerNews #FootballUpdate #BreakingNews #MatchDay"
        return fb_post
    except: return "BART Neural Link Severed."

# ────────────────────────────────────────────────
#               FEED & MAIN UI
# ────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_soccer_feed():
    sources = [("GOAL", "https://www.goal.com/en/feeds/news"), ("SKY", "https://www.skysports.com/rss/12040")]
    items = []
    seen = set()
    for name, url in sources:
        try:
            f = feedparser.parse(url)
            for e in f.entries:
                if e.link in seen: continue
                seen.add(e.link)
                items.append({"title": e.title.upper(), "link": e.link, "source": name, "id": hashlib.md5(e.link.encode()).hexdigest()})
        except: pass
    return items[:15]

st.title("⚽️ NEO-SCOUT • v8.6")
st.caption("FIRE-BART SYSTEM // FACEBOOK POST GENERATOR")

feed = get_soccer_feed()

for entry in feed:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(entry["title"])
            st.caption(f"📡 SOURCE: {entry['source']}")
        with col2:
            btn = st.button("🚀 SCAN & GENERATE", key=entry["id"])

        if btn:
            with st.spinner("🧬 Extracting & Formatting for Social..."):
                content, thumb = firecrawl_scrape(entry["link"])
                fb_final = bart_fb_summary(content, entry["title"])
                
                res_col1, res_col2 = st.columns([1, 2])
                with res_col1:
                    if thumb: st.image(thumb, use_container_width=True)
                
                with res_col2:
                    st.markdown("### 📱 FACEBOOK POST READY")
                    st.info("Copy the text below for your post:")
                    
                    # This is the "Copy and Paste" text box
                    # Streamlit's st.code has a built-in copy button in the top right!
                    st.code(fb_final, language="text")
                    
                    st.markdown(f'<div class="intel-box">{fb_final}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

st.sidebar.markdown("### 🛰 SYSTEM STATUS")
st.sidebar.write("🟢 Firecrawl: Active" if "FIRECRAWL_KEY" in st.secrets else "🔴 Firecrawl: Missing Key")
st.sidebar.write("🟢 BART-CNN: Active" if "HF_TOKEN" in st.secrets else "🔴 BART-CNN: Missing Token")
