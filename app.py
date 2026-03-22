import streamlit as st
import requests
import feedparser
import hashlib
from bs4 import BeautifulSoup
import time
import random

# --- CONFIG ---
st.set_page_config(page_title="NEO-SCOUT // V8.2", page_icon="📡", layout="wide")

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
    .node-label { color: #ff0055 !important; font-weight: bold; font-size: 0.8rem; border: 1px solid #ff0055; padding: 2px 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- SCRAPER & AI FUNCTIONS (Sanitized from previous step) ---
def scrape_intel(url):
    try:
        r = requests.get(url, timeout=7, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.content, 'html.parser')
        img = soup.find("meta", property="og:image")
        junk_keywords = ["attendance:", "vs", "kick-off", "referee:", "copyright"]
        paragraphs = []
        for p in soup.find_all('p'):
            text = " ".join(p.get_text().split())
            if len(text) > 80 and not any(junk in text.lower() for junk in junk_keywords):
                paragraphs.append(text)
        return " ".join(paragraphs[:4]), (img["content"] if img else None)
    except: return "", None

def query_ai_deep(text):
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    if "HF_TOKEN" not in st.secrets: return "ERROR: TOKEN_NOT_FOUND"
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    payload = {"inputs": text[:1024], "parameters": {"max_length": 150, "min_length": 60}}
    for _ in range(2):
        try:
            r = requests.post(API_URL, headers=headers, json=payload, timeout=15)
            res = r.json()
            if isinstance(res, list): return res[0]['summary_text']
            time.sleep(3)
        except: continue
    return f"[AUTO_GEN]: {'. '.join(text.split('. ')[:2])}."

# --- MULTI-SOURCE ENGINE ---
@st.cache_data(ttl=300)
def get_randomized_feed():
    # 10+ Diverse Global Sources
    feed_pool = [
        "https://www.goal.com/en/feeds/news",
        "https://www.skysports.com/rss/12040",
        "https://api.foxsports.com/v1/rss?partnerKey=zBaFxYLoverq&tag=soccer",
        "https://www.espn.com/espn/rss/soccer/news",
        "https://feeds.bbci.co.uk/sport/football/rss.xml",
        "https://www.fifa.com/rss/index.xml",
        "https://www.football365.com/feed",
        "https://www.90min.com/posts.rss",
        "https://www.caughtoffside.com/feed/",
        "https://www.theguardian.com/football/rss"
    ]
    
    # Shuffle the list of URLs so different sources appear at the top
    random.shuffle(feed_pool)
    
    full_stream = []
    # Only process the first 5-6 random sources to keep it fast
    for url in feed_pool[:6]: 
        try:
            f = feedparser.parse(url)
            source_name = url.split('/')[2].replace('www.', '').upper()
            for entry in f.entries[:3]: # Take 3 hottest stories from each random source
                full_stream.append({
                    "id": hashlib.md5(entry.link.encode()).hexdigest(),
                    "title": entry.title.upper(),
                    "link": entry.link,
                    "src": source_name
                })
        except: continue
    
    # Final shuffle of the individual stories
    random.shuffle(full_stream)
    return full_stream

# --- UI INTERFACE ---
st.title("📡 NEO-SCOUT // MULTI-NODE_V8.2")

# Refresh Logic
if st.button("🔄 RE-SCAN_SATELLITE_FEED"):
    st.cache_data.clear()
    st.rerun()

news_stream = get_randomized_feed()

st.write(f">> {len(news_stream)} INTEL_PACKETS_INTERCEPTED")

for item in news_stream:
    with st.container(border=True):
        st.markdown(f'<span class="node-label">NODE: {item["src"]}</span>', unsafe_allow_html=True)
        st.subheader(item['title'])
        
        if st.button("🔬 DECRYPT_REPORT", key=item['id']):
            with st.spinner(">> ANALYZING_SOURCE_DATA..."):
                clean_text, image = scrape_intel(item['link'])
                if image: st.image(image, use_container_width=True)
                
                if len(clean_text) > 100:
                    summary = query_ai_deep(clean_text)
                    st.info(summary)
                    
                    # Social Post Construction
                    tags = "#SportsNews #Viral #Football " + f"#{item['src'].split('.')[0]}"
                    st.text_area(">> BROADCAST_READY:", 
                                value=f"📡 {item['title']}\n\n{summary}\n\n{tags}", 
                                height=150)
                else:
                    st.error(">> ACCESS_DENIED: DATA_ENCRYPTED_OR_EMPTY")
        
        st.markdown(f"[>> SOURCE_LINK]({item['link']})")

st.markdown("---")
st.write(">> SYSTEM_ACTIVE // ALL_NODES_OPERATIONAL")
