import streamlit as st
import requests
import feedparser
import hashlib
from bs4 import BeautifulSoup
import time
import random

# --- CONFIG & STYLES ---
st.set_page_config(page_title="NEO-SCOUT // V8", page_icon="📡", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background-color: #050505; font-family: 'JetBrains Mono', monospace; }
    h1, h2, h3, p, span, div { color: #00ff41 !important; text-shadow: 0 0 5px #00ff41; }
    .stElementContainer div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #0a0a0a !important;
        border: 1px solid #00ff41 !important;
        box-shadow: 0 0 15px rgba(0, 255, 65, 0.2);
        padding: 20px; border-radius: 2px; margin-bottom: 20px;
    }
    .status-tag { font-size: 0.7rem; padding: 2px 5px; border: 1px solid #00ff41; margin-bottom: 10px; display: inline-block; }
    .char-counter { font-size: 0.8rem; color: #888 !important; text-align: right; }
    </style>
    """, unsafe_allow_html=True)

# --- ROBUST AI CORE ---
def query_ai_deep(text):
    """BART Summary with Exponential Backoff & Local Fallback."""
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    if "HF_TOKEN" not in st.secrets: return "ERROR: API_KEY_MISSING"
    
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    payload = {"inputs": text[:1500], "parameters": {"max_length": 160, "min_length": 70}}
    
    # Retry Logic with backoff
    wait_times = [5, 10, 15] 
    for wait in wait_times:
        try:
            r = requests.post(API_URL, headers=headers, json=payload, timeout=20)
            res = r.json()
            if isinstance(res, list): return res[0]['summary_text']
            if "estimated_time" in res:
                st.warning(f"SYSTEM_HEATING_UP: Retrying in {wait}s...")
                time.sleep(wait)
                continue
        except Exception:
            continue
            
    # LOCAL FALLBACK: Extractive summary (First 2 sentences)
    sentences = text.split('. ')
    return " [FALLBACK_ACTIVE]: " + ". ".join(sentences[:2]) + "."

# --- VIRAL TAG ENGINE ---
def generate_viral_tags(title):
    tags = ["#SportsTok", "#FootballNews", "#ViralSports", "#GameChanger"]
    if "TRANSFER" in title: tags += ["#TransferNews", "#HereWeGo"]
    return " ".join(random.sample(tags, k=min(len(tags), 5)))

# --- DATA FETCHING ---
@st.cache_data(ttl=600)
def get_live_stream():
    feeds = ["https://www.goal.com/en/feeds/news", "https://www.skysports.com/rss/12040"]
    stream = []
    for url in feeds:
        f = feedparser.parse(url)
        for entry in f.entries[:5]:
            stream.append({
                "id": hashlib.md5(entry.link.encode()).hexdigest(),
                "title": entry.title.upper(),
                "link": entry.link,
                "src": url.split('/')[2].upper()
            })
    return stream

def scrape_intel(url):
    try:
        r = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.content, 'html.parser')
        img = soup.find("meta", property="og:image")
        paras = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 50]
        return " ".join(paras[:5]), (img["content"] if img else None)
    except: return "", None

# --- UI MAIN ---
st.title("📡 NEO-SCOUT // V8.0_STABLE")

news_stream = get_live_stream()

for item in news_stream:
    with st.container(border=True):
        st.markdown(f'<div class="status-tag">NODE_{item["src"]}</div>', unsafe_allow_html=True)
        st.subheader(item['title'])
        
        if st.button("🔬 RUN_INTELLIGENCE_EXTRACTOR", key=item['id']):
            with st.spinner(">> INTERCEPTING_DATA_PACKETS..."):
                raw_text, image = scrape_intel(item['link'])
                if image: st.image(image, use_container_width=True)
                
                if len(raw_text) > 100:
                    summary = query_ai_deep(raw_text)
                    hashtags = generate_viral_tags(item['title'])
                    
                    full_post = f"⚽ {item['title']}\n\n{summary}\n\n{hashtags}"
                    
                    st.text_area(">> READY_FOR_SOCIAL:", value=full_post, height=180)
                    
                    # Character Counter Logic
                    char_count = len(full_post)
                    st.markdown(f'<div class="char-counter">CHAR_COUNT: {char_count} | '
                                f'X_LIMIT: {"✅" if char_count <= 280 else "❌"} | '
                                f'TIKTOK: ✅</div>', unsafe_allow_html=True)
                else:
                    st.error(">> ERROR: DATA_CORRUPTED_OR_TOO_SHORT")
        
        st.markdown(f"[>> SOURCE_LINK]({item['link']})")

st.markdown("---")
st.write(">> SYSTEM_STABLE // END_OF_LINE")
