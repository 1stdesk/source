import streamlit as st
import requests
import feedparser
import hashlib
import time
from duckduckgo_search import DDGS

# ────────────────────────────────────────────────
#               CYBERPUNK UI CONFIG
# ────────────────────────────────────────────────
st.set_page_config(page_title="NEO-SCOUT • v8.5", page_icon="⚡️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Roboto+Mono:wght@400;500&display=swap');
.stApp { background: linear-gradient(135deg, #0d0015, #1a0033); color: #e0e0ff; }
h1, h2 { font-family: 'Orbitron', sans-serif; background: linear-gradient(90deg, #00f0ff, #c300ff); 
         -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.stButton > button { border: 2px solid #00f0ff; color: #00f0ff; background: transparent; border-radius: 12px; font-weight: 600; width: 100%; }
.stButton > button:hover { background: linear-gradient(45deg, #00f0ff, #c300ff); color: #000; box-shadow: 0 0 15px #00f0ff; }
.card { background: rgba(20,10,40,0.8); backdrop-filter: blur(12px); border: 1px solid #00f0ff33; 
        border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem; }
.intel-box { background: rgba(25,10,45,0.95); border-left: 5px solid #c300ff; padding: 1.2rem; border-radius: 10px; border-right: 1px solid #c300ff33; }
.source-tag { background: #c300ff22; color: #c300ff; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; border: 1px solid #c300ff44; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#               NEURAL CORES (API)
# ────────────────────────────────────────────────

@st.cache_data(ttl=1800)
def firecrawl_scrape(url):
    """Bypasses bot detection using Firecrawl and returns clean Markdown."""
    if "FIRECRAWL_KEY" not in st.secrets:
        return "Critical Error: FIRECRAWL_KEY missing from secrets.", None
    
    headers = {
        "Authorization": f"Bearer {st.secrets['FIRECRAWL_KEY']}",
        "Content-Type": "application/json"
    }
    payload = {
        "url": url,
        "formats": ["markdown"],
        "onlyMainContent": True
    }
    try:
        r = requests.post("https://api.firecrawl.dev/v1/scrape", json=payload, headers=headers, timeout=30)
        if r.ok:
            data = r.json().get("data", {})
            markdown = data.get("markdown", "")
            meta = data.get("metadata", {})
            img = meta.get("og:image") or meta.get("twitter:image")
            return markdown, img
        return f"Firecrawl Error: {r.status_code}", None
    except Exception as e:
        return f"Link Failure: {str(e)}", None

@st.cache_data(ttl=1800)
def bart_summarize(text):
    """Processes raw text through Facebook BART-Large-CNN."""
    if not text or len(text) < 100:
        return "Insufficient data gathered for neural synthesis."
    if "HF_TOKEN" not in st.secrets:
        return "Neural Core Locked: Add HF_TOKEN to secrets."
    
    api_url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    
    # BART is optimized for ~1024 tokens. We send the first 3500 characters.
    payload = {
        "inputs": text[:3500],
        "parameters": {"max_length": 160, "min_length": 45, "do_sample": False}
    }
    try:
        r = requests.post(api_url, headers=headers, json=payload)
        if r.ok:
            return r.json()[0]['summary_text']
        return f"Neural Error: {r.status_code}"
    except:
        return "BART Neural Core Offline."

@st.cache_data(ttl=1800)
def get_related_intel(title):
    """Uses DDG to find 2 more relevant pictures/news based on title."""
    try:
        with DDGS() as ddgs:
            # Optimized query for soccer/football visuals
            query = f"{title} soccer match photo -stock"
            results = list(ddgs.images(query, max_results=2))
            return [r['image'] for r in results if 'image' in r]
    except:
        return []

# ────────────────────────────────────────────────
#               FEED ENGINE
# ────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_soccer_feed():
    sources = [
        ("GOAL", "https://www.goal.com/en/feeds/news"),
        ("SKY", "https://www.skysports.com/rss/12040"),
        ("BBC", "https://feeds.bbci.co.uk/sport/football/rss.xml"),
        ("GUARDIAN", "https://www.theguardian.com/football/rss"),
    ]
    items = []
    seen = set()
    for name, url in sources:
        try:
            f = feedparser.parse(url)
            for e in f.entries:
                title = e.title.strip()
                # Basic soccer filter
                if not any(k in title.lower() for k in ["football","soccer","league","goal","transfer"]):
                    continue
                if e.link in seen: continue
                seen.add(e.link)
                items.append({
                    "title": title.upper(),
                    "link": e.link,
                    "source": name,
                    "id": hashlib.md5(e.link.encode()).hexdigest()
                })
        except: pass
    return items[:30]

# ────────────────────────────────────────────────
#               MAIN INTERFACE
# ────────────────────────────────────────────────
st.title("⚡️ NEO-SCOUT • v8.5 • NEURAL")
st.caption("FIRECRAWL EXTRACTOR // BART-CNN SUMMARIZER // DDG OSINT")

if st.button("⟲ REFRESH SATELLITE FEED"):
    get_soccer_feed.clear()
    st.rerun()

feed = get_soccer_feed()

for entry in feed:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        
        col_header, col_meta = st.columns([4, 1])
        with col_header:
            st.subheader(entry["title"])
        with col_meta:
            st.markdown(f"<div style='text-align:right'><span class='source-tag'>{entry['source']}</span></div>", unsafe_allow_html=True)

        # Action Area
        if st.button("🚀 DEEP SCAN ARTICLE", key=entry["id"]):
            with st.spinner("⚡️ PENETRATING SOURCE..."):
                # 1. Scrape
                raw_markdown, head_img = firecrawl_scrape(entry["link"])
                
                # 2. Summarize
                summary = bart_summarize(raw_markdown)
                
                # 3. Extra Intel
                extra_pics = get_related_intel(entry["title"])

                # Display Results
                c1, c2 = st.columns([1, 2])
                with c1:
                    if head_img:
                        st.image(head_img, caption="PRIMARY SOURCE IMAGE", use_container_width=True)
                    
                    if extra_pics:
                        st.markdown("**📡 RELATED INTEL IMAGES**")
                        pic_cols = st.columns(len(extra_pics))
                        for idx, p in enumerate(extra_pics):
                            pic_cols[idx].image(p, use_container_width=True)

                with c2:
                    st.markdown(f"""
                    <div class="intel-box">
                        <strong>🧬 BART NEURAL SUMMARY v8.5</strong><br><br>
                        {summary}
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(f"<br>[→ ACCESS FULL DATA STREAM]({entry['link']})", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

st.sidebar.markdown("### 🛠 SYSTEM STATUS")
if "FIRECRAWL_KEY" in st.secrets and "HF_TOKEN" in st.secrets:
    st.sidebar.success("ONLINE: API Links Secure")
else:
    st.sidebar.error("OFFLINE: Check Secrets.toml")
