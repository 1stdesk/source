import streamlit as st
import requests
import feedparser
import hashlib
import time

# ────────────────────────────────────────────────
#               CYBERPUNK UI CONFIG
# ────────────────────────────────────────────────
st.set_page_config(page_title="NEO-SCOUT • v9.0", page_icon="⚽️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Roboto+Mono:wght@400;500&display=swap');
.stApp { background: linear-gradient(135deg, #0d0015, #120022); color: #e0e0ff; }
h1, h2 { font-family: 'Orbitron', sans-serif; background: linear-gradient(90deg, #00f0ff, #c300ff); 
         -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.stButton > button { border: 2px solid #00f0ff; color: #00f0ff; background: transparent; border-radius: 12px; font-weight: 600; width: 100%; transition: 0.3s; }
.stButton > button:hover { background: linear-gradient(45deg, #00f0ff, #c300ff); color: #000; box-shadow: 0 0 20px #00f0ff; }
.card { background: rgba(30,10,60,0.8); backdrop-filter: blur(20px); border: 1px solid #00f0ff11; 
        border-radius: 20px; padding: 1.8rem; margin-bottom: 1.5rem; border-left: 4px solid #00f0ff33; }
.source-tag { background: #c300ff22; color: #c300ff; padding: 4px 12px; border-radius: 8px; font-size: 0.7rem; font-weight: bold; border: 1px solid #c300ff44; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#               NEURAL ENGINE v9.0
# ────────────────────────────────────────────────

@st.cache_data(ttl=1800)
def firecrawl_scrape(url):
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
    """Refined summarizer with persistent loading retry."""
    if not text or len(text) < 200: return "⚠️ Error: Article content too short for neural synthesis."
    
    api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    payload = {
        "inputs": text[:4500],
        "parameters": {"max_length": 100, "min_length": 65, "repetition_penalty": 2.8},
        "options": {"wait_for_model": True}
    }

    # Intelligent Retry Loop
    for attempt in range(5): # Up to 5 attempts for cold models
        try:
            r = requests.post(api_url, headers=headers, json=payload, timeout=60)
            res = r.json()
            
            # Scenario A: Success
            if r.status_code == 200 and isinstance(res, list):
                summary = res[0]['summary_text'].replace(' .', '.').strip()
                return f"🚨 SOCCER UPDATE: {title}\n\n{summary}\n\n⚽ #SoccerNews #FootballUpdate #BreakingNews #MatchDay"
            
            # Scenario B: Model is loading (Common Error)
            elif r.status_code == 503 or "estimated_time" in str(res):
                wait_time = res.get("estimated_time", 20)
                st.info(f"🧠 NEURAL CORE WAKING UP: Estimated {int(wait_time)}s remaining...")
                time.sleep(min(wait_time, 30)) # Wait but cap it to 30s per loop
                continue
            
            # Scenario C: Rate Limit
            elif r.status_code == 429:
                st.warning("⚠️ High traffic. Retrying in 5s...")
                time.sleep(5)
                continue
        except Exception as e:
            time.sleep(2)
            
    return "❌ Connection timeout. The Neural Core is currently overloaded. Please try again in 30 seconds."

# ────────────────────────────────────────────────
#               ULTRA SOURCE ENGINE
# ────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_ultra_feed():
    sources = [
        ("GOAL", "https://www.goal.com/en/feeds/news"),
        ("SKY", "https://www.skysports.com/rss/12040"),
        ("BBC", "https://feeds.bbci.co.uk/sport/football/rss.xml"),
        ("GUARDIAN", "https://www.theguardian.com/football/rss"),
        ("ESPN", "https://www.espn.com/espn/rss/soccer/news"),
        ("90MIN", "https://www.90min.com/posts.rss")
    ]
    items = []
    seen = set()
    for name, url in sources:
        try:
            f = feedparser.parse(url)
            for e in f.entries:
                if e.link not in seen:
                    seen.add(e.link)
                    items.append({"title": e.title.upper(), "link": e.link, "source": name, "id": hashlib.md5(e.link.encode()).hexdigest()})
        except: pass
    return items[:30]

# ────────────────────────────────────────────────
#               MAIN INTERFACE
# ────────────────────────────────────────────────
st.title("⚡️ NEO-SCOUT • v9.0")
st.caption("STABLE NEURAL BRIDGE // DUAL-SENTENCE FB GENERATOR")

feed = get_ultra_feed()
search = st.text_input("📡 FILTER GLOBAL INTEL...", "").upper()
if search: feed = [f for f in feed if search in f['title']]

for entry in feed:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        c_title, c_btn = st.columns([4, 1])
        
        with c_title:
            st.markdown(f"**{entry['title']}**")
            st.markdown(f"<span class='source-tag'>{entry['source']}</span>", unsafe_allow_html=True)
        
        with c_btn:
            if st.button("🚀 SCAN", key=entry["id"]):
                with st.spinner("⚡️ Scraping Source..."):
                    content, thumb = firecrawl_scrape(entry["link"])
                
                if content:
                    fb_post = bart_dual_sentence(content, entry["title"])
                    
                    res1, res2 = st.columns([1, 2])
                    with res1:
                        if thumb: st.image(thumb, use_container_width=True)
                        else: st.warning("No image found.")
                    with res2:
                        st.markdown("### 📱 FACEBOOK POST")
                        st.code(fb_post, language="text")
                else:
                    st.error("🚫 Source blocked the scan. Try another article.")
        st.markdown('</div>', unsafe_allow_html=True)
