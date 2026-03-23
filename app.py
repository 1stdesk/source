import streamlit as st
import requests
import feedparser
import hashlib
import time
from duckduckgo_search import DDGS

# ────────────────────────────────────────────────
#               CYBERPUNK UI CONFIG
# ────────────────────────────────────────────────
st.set_page_config(page_title="NEO-SCOUT • v8.7", page_icon="⚽️", layout="wide")

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
.fb-ready { background: #1877F222; border: 1px dashed #1877F2; padding: 15px; border-radius: 10px; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#               PRO-LEVEL NEURAL CORE
# ────────────────────────────────────────────────

@st.cache_data(ttl=1800)
def firecrawl_scrape(url):
    """Scrapes clean Markdown using Firecrawl."""
    if "FIRECRAWL_KEY" not in st.secrets:
        return "Missing FIRECRAWL_KEY", None
    headers = {"Authorization": f"Bearer {st.secrets['FIRECRAWL_KEY']}", "Content-Type": "application/json"}
    payload = {"url": url, "formats": ["markdown"], "onlyMainContent": True}
    try:
        r = requests.post("https://api.firecrawl.dev/v1/scrape", json=payload, headers=headers, timeout=30)
        if r.ok:
            data = r.json().get("data", {})
            img = data.get("metadata", {}).get("og:image")
            return data.get("markdown", ""), img
        return None, None
    except: return None, None

def bart_detailed_summary(text, title):
    """
    Enhanced BART summarizer with 'Wait for Model' logic and 
    richer detail parameters to prevent 'Neural Timeout'.
    """
    if not text or len(text) < 200:
        return "⚠️ Data stream insufficient. The article might be behind a paywall or too short."
    
    api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    
    # parameters tuned for BETTER, LONGER summaries
    payload = {
        "inputs": text[:4000],
        "parameters": {
            "max_length": 250,      # Increased for more detail
            "min_length": 100,     # Forced depth
            "do_sample": False,
            "repetition_penalty": 1.2
        },
        "options": {
            "wait_for_model": True  # CRITICAL: Prevents 'Neural Core Timeout'
        }
    }
    
    try:
        # Initial attempt
        r = requests.post(api_url, headers=headers, json=payload)
        res = r.json()
        
        if r.status_code == 200 and isinstance(res, list):
            summary = res[0]['summary_text']
            # Format for Facebook
            fb_post = f"🚨 SOCCER UPDATE: {title}\n\n{summary}\n\n⚽ #SoccerNews #FootballUpdate #BreakingNews #MatchDay"
            return fb_post
        elif "estimated_time" in res:
            # If model is still loading, wait and try once more
            wait_time = res["estimated_time"]
            st.warning(f"🧠 Neural Core is warming up... waiting {int(wait_time)}s")
            time.sleep(wait_time)
            r = requests.post(api_url, headers=headers, json=payload)
            return r.json()[0]['summary_text']
        else:
            return f"❌ Neural Core Busy: {res.get('error', 'Unknown Error')}"
    except Exception as e:
        return f"🛠️ System Error: {str(e)}"

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

st.title("⚡️ NEO-SCOUT • v8.7")
st.caption("ENHANCED NEURAL RELIABILITY // FB POST GENERATOR")

feed = get_soccer_feed()

for entry in feed:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader(entry["title"])
            st.caption(f"📡 SOURCE: {entry['source']}")
        with col2:
            btn = st.button("🚀 DEEP ANALYSIS", key=entry["id"])

        if btn:
            with st.spinner("🧬 Extracting clean data via Firecrawl..."):
                content, thumb = firecrawl_scrape(entry["link"])
            
            if content:
                with st.spinner("🧠 Generating detailed neural summary..."):
                    fb_final = bart_detailed_summary(content, entry["title"])
                
                res_col1, res_col2 = st.columns([1, 2])
                with res_col1:
                    if thumb: st.image(thumb, use_container_width=True)
                
                with res_col2:
                    st.markdown("### 📱 FACEBOOK POST READY")
                    st.code(fb_final, language="text")
            else:
                st.error("🚫 Firecrawl could not reach the article. It may be restricted.")
        
        st.markdown('</div>', unsafe_allow_html=True)

st.sidebar.markdown("### 🛰 SYSTEM STATUS")
st.sidebar.write("🟢 Firecrawl: Connected" if "FIRECRAWL_KEY" in st.secrets else "🔴 Firecrawl: Key Missing")
st.sidebar.write("🟢 BART-CNN: Active" if "HF_TOKEN" in st.secrets else "🔴 BART-CNN: Token Missing")
