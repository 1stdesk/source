import streamlit as st
import requests
import feedparser
import hashlib
from bs4 import BeautifulSoup
import time
import random

# --- FUTURISTIC UI CONFIG ---
st.set_page_config(page_title="NEO-SCOUT // VIRAL_EDITION", page_icon="📡", layout="wide")

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
    .stButton>button {
        background-color: transparent !important; color: #00ff41 !important;
        border: 1px solid #00ff41 !important; font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase; letter-spacing: 2px; transition: 0.3s; border-radius: 0px;
    }
    .stButton>button:hover { background-color: #00ff41 !important; color: #000 !important; box-shadow: 0 0 20px #00ff41; }
    .intel-box {
        background-color: #001a00; border-left: 4px solid #00ff41;
        padding: 15px; margin: 10px 0; font-size: 0.95rem; color: #d1ffd1 !important; line-height: 1.6;
    }
    .hashtag-cluster { color: #00d4ff !important; font-weight: bold; margin-top: 10px; font-size: 0.85rem; }
    </style>
    """, unsafe_allow_html=True)

# --- VIRAL HASHTAG ENGINE ---
def generate_viral_tags(title):
    """Generates a mix of trending TikTok, FB, and Podcast hashtags."""
    base_tags = ["#SportsTok", "#FootballNews", "#SoccerDaily", "#GameChanger", "#SportsPodcast"]
    viral_platforms = ["#ESPNPlus", "#FBPresents", "#ViralSports", "#NewHeights", "#PatMcAfeeShow"]
    
    # Contextual tags based on keywords
    context_tags = []
    if "TRANSFER" in title.upper(): context_tags.extend(["#TransferWindow", "#HereWeGo"])
    if "GOAL" in title.upper() or "WIN" in title.upper(): context_tags.extend(["#Golazo", "#Winning"])
    if "INJURY" in title.upper(): context_tags.extend(["#BreakingNews", "#FantasyFootball"])

    # Combine and shuffle
    all_tags = list(set(base_tags + viral_platforms + context_tags))
    return " ".join(random.sample(all_tags, k=min(len(all_tags), 8)))

# --- AI CORE ---
def query_ai_deep(text):
    API_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-cnn"
    if "HF_TOKEN" not in st.secrets: return "ERROR: TOKEN_NOT_FOUND"
    
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    payload = {
        "inputs": text[:1500],
        "parameters": {"do_sample": False, "max_length": 180, "min_length": 90, "repetition_penalty": 1.3}
    }
    for i in range(3):
        try:
            r = requests.post(API_URL, headers=headers, json=payload, timeout=15)
            res = r.json()
            if isinstance(res, dict) and "estimated_time" in res:
                time.sleep(5); continue
            return res[0]['summary_text']
        except: continue
    return "SYSTEM_TIMEOUT"

# --- DATA STREAM ---
@st.cache_data(ttl=300)
def get_live_stream():
    feeds = ["https://www.goal.com/en/feeds/news", "https://www.skysports.com/rss/12040"]
    stream = []
    for url in feeds:
        f = feedparser.parse(url)
        for entry in f.entries[:6]:
            stream.append({"id": hashlib.md5(entry.link.encode()).hexdigest(), 
                           "title": entry.title.upper(), "link": entry.link, "src": url.split('/')[2].upper()})
    return stream

def scrape_intel(url):
    try:
        r = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.content, 'html.parser')
        img = soup.find("meta", property="og:image")
        paras = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60]
        return " ".join(paras[:5]), (img["content"] if img else None)
    except: return "", None

# --- MAIN INTERFACE ---
st.title("📡 NEO-SCOUT // VIRAL_AGGREGATOR_V7")

# Global Refresh
if st.button("🔄 REFRESH_SYSTEM_FEED"):
    st.cache_data.clear()
    st.rerun()

news_stream = get_live_stream()

for item in news_stream:
    with st.container(border=True):
        st.write(f"NODE: {item['src']}")
        st.subheader(item['title'])
        
        if st.button("🔬 GENERATE_DEEP_REPORT", key=item['id']):
            with st.spinner(">> DECRYPTING_AND_ANALYZING..."):
                raw_text, image = scrape_intel(item['link'])
                if image: st.image(image, use_container_width=True)
                
                if len(raw_text) > 150:
                    summary = query_ai_deep(raw_text)
                    hashtags = generate_viral_tags(item['title'])
                    
                    st.markdown(f"""
                        <div class="intel-box">
                            <strong>[AI_SCOUT_REPORT]</strong><br><br>
                            {summary}<br><br>
                            <div class="hashtag-cluster">{hashtags}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Ready for Social Media
                    st.text_area(">> READY_FOR_UPLOAD:", 
                                value=f"⚽ {item['title']}\n\n{summary}\n\n{hashtags}\n\nSource: {item['link']}", 
                                height=150)
                else:
                    st.write(">> ERROR: INSUFFICIENT_DATA")
        
        st.markdown(f"[>> ACCESS_SOURCE]({item['link']})")

st.markdown("---")
st.write(">> SYSTEM_ONLINE // END_OF_LINE")
