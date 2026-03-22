import streamlit as st
import requests
import feedparser
import hashlib
from bs4 import BeautifulSoup
import time
import random

# --- CYBERPUNK UI ---
st.set_page_config(page_title="NEO-SCOUT // V10_STABLE", page_icon="📡", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background-color: #050505 !important; font-family: 'JetBrains Mono', monospace; }
    h1, h2, h3, .stMarkdown p { color: #00ff41 !important; text-shadow: 0 0 10px #00ff41; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #080808 !important; border: 1px solid #00ff41 !important;
        box-shadow: 0 0 20px rgba(0, 255, 65, 0.1); padding: 25px; margin-bottom: 25px;
    }
    .stButton>button {
        background-color: transparent !important; color: #00ff41 !important;
        border: 1px solid #00ff41 !important; border-radius: 0px; width: 100%; transition: 0.4s;
        font-weight: bold; letter-spacing: 2px;
    }
    .stButton>button:hover { background-color: #00ff41 !important; color: #000 !important; box-shadow: 0 0 30px #00ff41; }
    .intel-box { background-color: #001a00; border: 1px solid #00ff41; padding: 20px; color: #d1ffd1 !important; font-size: 1rem; line-height: 1.6; }
    </style>
    """, unsafe_allow_html=True)

# --- REINFORCED AI ENGINE ---
def query_ai_scout(text):
    # USE THE 2026 ROUTER URL
    API_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-cnn"
    
    if "HF_TOKEN" not in st.secrets:
        return "FATAL_ERROR: HF_TOKEN_NOT_FOUND_IN_SECRETS"
    
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}", "Content-Type": "application/json"}
    payload = {
        "inputs": text[:1500],
        "parameters": {"max_length": 180, "min_length": 80, "do_sample": False, "repetition_penalty": 1.2}
    }

    # REFRESH LOOP: Prevents Signal_Interrupted: 0
    for attempt in range(3):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
            result = response.json()
            
            if isinstance(result, dict) and "estimated_time" in result:
                st.warning(f"⏳ MODEL_WAKING_UP... ATTEMPT {attempt+1}/3 ({int(result['estimated_time'])}s)")
                time.sleep(10) # Wait for model to load
                continue
            
            if isinstance(result, list) and len(result) > 0:
                return result[0]['summary_text']
            
            return f"API_RESPONSE_ERROR: {result}"
        except requests.exceptions.Timeout:
            continue
        except Exception as e:
            return f"SIGNAL_CRITICAL_FAILURE: {str(e)}"
            
    return "😴 AI_FAILED_TO_WAKE_UP. TRY_AGAIN_IN_60S."

# --- BULLETPROOF SCRAPER ---
def fetch_article_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,xml;q=0.9,image/avif,webp,*/*;q=0.8"
    }
    try:
        r = requests.get(url, headers=headers, timeout=12)
        soup = BeautifulSoup(r.content, 'html.parser')
        # Scrape 8 paragraphs for 'Deeper' context
        paras = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 70]
        return " ".join(paras[:8])
    except:
        return ""

# --- DATA MATRIX (20 NODES) ---
@st.cache_data(ttl=600)
def get_global_news():
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
    matrix = []
    for url in sources:
        try:
            f = feedparser.parse(url)
            for entry in f.entries[:2]:
                matrix.append({
                    "id": hashlib.md5(entry.link.encode()).hexdigest(),
                    "title": entry.title.upper(),
                    "link": entry.link,
                    "source": url.split('/')[2].upper()
                })
        except: continue
    return matrix

# --- MAIN INTERFACE ---
st.title("🛰️ NEO-SCOUT // FINAL_STABLE_V10")

if st.button("🔄 RESYNC_GLOBAL_NODES"):
    st.cache_data.clear()
    st.rerun()

news_list = get_global_news()
filter_q = st.text_input(">> SCAN_FILTER (TEAM/PLAYER):", "").upper()

for item in news_list:
    if filter_q and filter_q not in item['title']: continue
    
    with st.container(border=True):
        st.write(f"NODE: {item['source']}")
        st.subheader(item['title'])
        
        if st.button("🔬 EXTRACT_DEEP_INTEL", key=item['id']):
            with st.spinner(">> INTERCEPTING_PACKETS..."):
                raw_intel = fetch_article_data(item['link'])
                
                if len(raw_intel) > 200:
                    summary = query_ai_scout(raw_intel)
                    tags = "#SportsTok #FootballDaily #NewHeights #ViralSoccer #SkySports"
                    
                    st.markdown(f"""
                        <div class="intel-box">
                            <strong>[DEEP_SCOUT_REPORT]</strong><br><br>{summary}<br><br>
                            <span style="color:#00d4ff;">{tags}</span>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.text_area(">> SHARE_READY_INTEL:", 
                                value=f"🚨 PRO SCOUT: {item['title']}\n\n{summary}\n\n{tags}\n\nSource: {item['link']}", 
                                height=160)
                else:
                    st.error(">> ACCESS_DENIED: DATA_PACKET_EMPTY_OR_PAYWALLED")
        
        st.caption(f"[>> ACCESS_SOURCE_NODE]({item['link']})")

st.markdown("---")
st.write(">> SYSTEM_STABLE // 20_NODES_ACTIVE")
