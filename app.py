import streamlit as st
import requests
import feedparser
import hashlib
from bs4 import BeautifulSoup
import time
import random
import re

# --- CONFIG ---
st.set_page_config(page_title="NEO-SCOUT // V8.1_CLEAN", page_icon="📡", layout="wide")

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
    .intel-box {
        background-color: #001a00; border-left: 4px solid #00ff41;
        padding: 15px; margin: 10px 0; font-size: 0.95rem; color: #d1ffd1 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SANITIZED SCRAPER ---
def scrape_intel(url):
    """Scrapes and purges 'Noise' like attendance, vs stats, and ads."""
    try:
        r = requests.get(url, timeout=7, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Metadata image
        img = soup.find("meta", property="og:image")
        img_url = img["content"] if img else None

        # Content Extraction & Cleaning
        # We target specific junk keywords common in sports reporting
        junk_keywords = ["attendance:", "vs", "kick-off", "referee:", "match report", "copyright"]
        
        paragraphs = []
        for p in soup.find_all('p'):
            text = p.get_text().strip()
            
            # 1. Remove messy whitespace/tabs
            text = " ".join(text.split())
            
            # 2. Filter: Must be long enough AND not contain junk keywords
            if len(text) > 80 and not any(junk in text.lower() for junk in junk_keywords):
                paragraphs.append(text)
        
        # Combine the best 4 paragraphs for the AI to analyze
        sanitized_content = " ".join(paragraphs[:4])
        return sanitized_content, img_url
    except Exception as e:
        return "", None

# --- AI CORE WITH BACKOFF ---
def query_ai_deep(text):
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    if "HF_TOKEN" not in st.secrets: return "ERROR: TOKEN_NOT_FOUND"
    
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    payload = {
        "inputs": text[:1024], # BART limit
        "parameters": {"do_sample": False, "max_length": 150, "min_length": 60}
    }

    # Retry logic if model is loading
    for _ in range(3):
        try:
            r = requests.post(API_URL, headers=headers, json=payload, timeout=15)
            res = r.json()
            if isinstance(res, list): return res[0]['summary_text']
            time.sleep(5)
        except: continue
        
    # Smart Fallback: If AI fails, take the first two cleaned sentences
    sentences = text.split(". ")
    return f"[AUTO_GEN]: {'. '.join(sentences[:2])}."

# --- VIRAL TAG ENGINE ---
def generate_viral_tags(title):
    base = ["#SportsTok", "#FootballNews", "#ViralSports", "#GameChanger"]
    if "CELTIC" in title: base += ["#CelticFC", "#SPFL"]
    if "BEATEN" in title or "DROP" in title: base += ["#ShockResult", "#TitleRace"]
    return " ".join(random.sample(list(set(base)), k=min(len(base), 6)))

# --- FEED HANDLER ---
@st.cache_data(ttl=600)
def get_live_stream():
    feeds = ["https://www.goal.com/en/feeds/news", "https://www.skysports.com/rss/12040"]
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

# --- UI MAIN ---
st.title("📡 NEO-SCOUT // V8.1_CLEAN_EDITION")

if st.button("🔄 SYSTEM_RELOAD"):
    st.cache_data.clear()
    st.rerun()

for item in get_live_stream():
    with st.container(border=True):
        st.write(f"NODE: {item['src']}")
        st.subheader(item['title'])
        
        if st.button("🔬 EXTRACT_INTEL", key=item['id']):
            with st.spinner(">> PURGING_NOISE_AND_ANALYZING..."):
                clean_text, image = scrape_intel(item['link'])
                
                if image: st.image(image, use_container_width=True)
                
                if len(clean_text) > 100:
                    summary = query_ai_deep(clean_text)
                    hashtags = generate_viral_tags(item['title'])
                    
                    st.markdown(f"""
                        <div class="intel-box">
                            <strong>[AI_SCOUT_REPORT]</strong><br><br>
                            {summary}<br><br>
                            <span style="color: #00d4ff;">{hashtags}</span>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.text_area(">> COPY_FOR_UPLOAD:", 
                                value=f"⚽ {item['title']}\n\n{summary}\n\n{hashtags}\n\nRead more: {item['link']}", 
                                height=200)
                else:
                    st.warning(">> ERROR: SOURCE_PROTECTED_OR_NO_TEXT")

st.markdown("---")
st.write(">> SYSTEM_ONLINE // NOISE_FILTER_ACTIVE")
