import streamlit as st
import requests
import feedparser
import hashlib
from bs4 import BeautifulSoup
import time
import random

# --- FUTURISTIC UI CONFIG ---
st.set_page_config(page_title="NEO-SCOUT // 20_SOURCE_MATRIX", page_icon="🛰️", layout="wide")

# Matrix Green & Cyberpunk Pink Theme
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    
    .stApp { background-color: #050505 !important; font-family: 'JetBrains Mono', monospace; }
    
    h1, h2, h3, .stMarkdown p, .stCaption { 
        color: #00ff41 !important; 
        text-shadow: 0 0 8px rgba(0, 255, 65, 0.6); 
    }
    
    /* Futuristic Card Borders */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #0a0a0a !important;
        border: 1px solid #00ff41 !important;
        box-shadow: 0 0 15px rgba(0, 255, 65, 0.2);
        padding: 20px;
        margin-bottom: 20px;
        border-radius: 4px;
    }

    /* Terminal Style Buttons */
    .stButton>button {
        background-color: transparent !important;
        color: #00ff41 !important;
        border: 1px solid #00ff41 !important;
        border-radius: 0px;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #00ff41 !important;
        color: #000 !important;
        box-shadow: 0 0 20px #00ff41;
    }

    .intel-box {
        background-color: #001a00;
        border-left: 5px solid #00ff41;
        padding: 20px;
        color: #d1ffd1 !important;
        margin: 10px 0;
    }
    
    .viral-title { color: #ff00ff !important; font-weight: bold; font-style: italic; }
    .hashtag-cluster { color: #00d4ff !important; font-weight: bold; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- VIRAL ENGINE ---
def generate_viral_metadata(title):
    tags = ["#SportsTok", "#FootballNews", "#SoccerDaily", "#NewHeights", "#PatMcAfeeShow", "#ESPNPlus", "#ViralSports", "#TransferTalk"]
    hooks = [
        f"🚨 URGENT: {title} 😱",
        f"The TRUTH about {title}... 🤫",
        f"POV: You just heard {title} ⚽🔥",
        f"Why NO ONE is talking about {title} 🤯"
    ]
    return " ".join(random.sample(tags, 6)), random.sample(hooks, 3)

# --- AI CORE (2026 ROUTER UPGRADE) ---
def query_ai_deep(text):
    # Updated to 2026 serverless router endpoint
    API_URL = "https://router.huggingface.co/hf-inference/v1/chat/completions"
    if "HF_TOKEN" not in st.secrets: return "ERROR: TOKEN_NOT_FOUND"
    
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}", "Content-Type": "application/json"}
    
    # Using a 2026-standard model for high-speed summarization
    payload = {
        "model": "facebook/bart-large-cnn", 
        "messages": [{"role": "user", "content": f"Summarize this sports news in 3 hard-hitting sentences: {text[:2000]}"}],
        "max_tokens": 150
    }

    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=20)
        res = r.json()
        return res['choices'][0]['message']['content']
    except:
        return "SIGNAL_LOST: MODEL_BUSY. PLEASE_RETRY."

# --- HEAVY-DUTY SCRAPER ---
def scrape_intel(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Referer": "https://www.google.com/"
    }
    try:
        r = requests.get(url, timeout=10, headers=headers)
        soup = BeautifulSoup(r.content, 'html.parser')
        # Filter for quality paragraphs only
        paras = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 70]
        text = " ".join(paras[:8])
        return text if len(text) > 150 else ""
    except: return ""

# --- THE 20-SOURCE MATRIX ---
@st.cache_data(ttl=600)
def get_matrix_feed():
    sources = [
        "https://www.goal.com/en/feeds/news", "https://www.skysports.com/rss/12040",
        "https://www.theguardian.com/football/rss", "https://www.espn.com/espn/rss/soccer/news",
        "https://www.bbc.com/sport/football/rss.xml", "https://www.football365.com/news/feed",
        "https://www.transfermarkt.co.uk/rss/news", "https://www.mirror.co.uk/sport/football/rss.xml",
        "https://www.football-espana.net/feed", "https://www.getfootballnewsfrance.com/feed",
        "https://www.getfootballnewsgermany.com/feed", "https://www.football-italia.net/feed",
        "https://worldsoccertalk.com/feed", "https://www.tribalfootball.com/rss.xml",
        "https://www.90min.com/posts.rss", "https://www.caughtoffside.com/feed",
        "https://www.standard.co.uk/sport/football/rss", "https://www.independent.co.uk/sport/football/rss",
        "https://theathletic.com/rss", "https://www.dailymail.co.uk/sport/football/index.rss"
    ]
    stream = []
    for url in sources:
        try:
            f = feedparser.parse(url)
            for entry in f.entries[:2]:
                stream.append({
                    "id": hashlib.md5(entry.link.encode()).hexdigest(),
                    "title": entry.title.upper(),
                    "link": entry.link,
                    "src": url.split('/')[2].upper()
                })
        except: continue
    return stream

# --- MAIN INTERFACE ---
st.title("🛰️ NEO-SCOUT // 20_SOURCE_MATRIX")

if st.button("🔄 REFRESH_SYSTEM_FEED"):
    st.cache_data.clear()
    st.rerun()

search = st.text_input(">> FILTER_QUERY (TEAM/PLAYER):", "").upper()
news_stream = get_matrix_feed()

for item in news_stream:
    if search and search not in item['title']: continue
    
    with st.container(border=True):
        st.write(f"NODE: {item['src']}")
        st.subheader(item['title'])
        
        if st.button("🔬 EXTRACT_DEEP_INTEL", key=item['id']):
            with st.spinner(">> BYPASSING_FIREWALLS..."):
                raw_text = scrape_intel(item['link'])
                
                if raw_text:
                    summary = query_ai_deep(raw_text)
                    tags, hooks = generate_viral_metadata(item['title'])
                    
                    st.markdown(f"""
                        <div class="intel-box">
                            <strong>[SCOUT_REPORT]</strong><br>{summary}<br><br>
                            <strong>[VIRAL_HOOKS]</strong><br>
                            <span class="viral-title">1. {hooks[0]}</span><br>
                            <span class="viral-title">2. {hooks[1]}</span><br>
                            <div class="hashtag-cluster">{tags}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.text_area(">> EXPORT_FOR_TIKTOK_FB:", 
                                value=f"🎥 Hook: {hooks[0]}\n\n⚽ News: {summary}\n\n{tags}\n\nLink: {item['link']}", 
                                height=160)
                else:
                    st.error(">> ACCESS_DENIED: DATA_PACKET_TOO_SMALL_OR_PAYWALLED")
        
        st.caption(f"[>> SOURCE_NODE]({item['link']})")

st.markdown("---")
st.write(">> 20_NODES_STABLE // END_OF_LINE")
