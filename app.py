import streamlit as st
import requests
import feedparser
import hashlib
from bs4 import BeautifulSoup
import time
import random

# --- FUTURISTIC UI CONFIG ---
st.set_page_config(page_title="NEO-SCOUT // 20_SOURCE_MATRIX", page_icon="🛰️", layout="wide")

# Fixed CSS: Removed 'div' selector to prevent black screen overlay
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    
    .stApp { background-color: #050505 !important; font-family: 'JetBrains Mono', monospace; }
    
    /* Target only specific text elements to avoid hiding UI */
    h1, h2, h3, .stMarkdown p, .stCaption { 
        color: #00ff41 !important; 
        text-shadow: 0 0 5px rgba(0, 255, 65, 0.5); 
    }
    
    /* Neon Container Styling */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #0a0a0a !important;
        border: 1px solid #00ff41 !important;
        box-shadow: 0 0 10px rgba(0, 255, 65, 0.1);
        padding: 15px;
        margin-bottom: 15px;
    }

    /* Matrix Buttons */
    .stButton>button {
        background-color: transparent !important;
        color: #00ff41 !important;
        border: 1px solid #00ff41 !important;
        border-radius: 0px;
        width: 100%;
        transition: 0.2s;
    }
    .stButton>button:hover {
        background-color: #00ff41 !important;
        color: #000 !important;
        box-shadow: 0 0 15px #00ff41;
    }

    .intel-box {
        background-color: #001500;
        border-left: 3px solid #00ff41;
        padding: 15px;
        color: #d1ffd1 !important;
        font-size: 0.9rem;
    }
    
    .viral-title { color: #ff00ff !important; font-weight: bold; }
    .hashtag-cluster { color: #00d4ff !important; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

# --- VIRAL ENGINE ---
def generate_viral_intel(title):
    tags = ["#SportsTok", "#FootballNews", "#SoccerDaily", "#NewHeights", "#PatMcAfeeShow", "#ESPNPlus", "#ViralSports", "#TransferTalk"]
    hooks = [
        f"🚨 LEAKED: {title} 😱",
        f"The TRUTH behind {title} 🤫",
        f"POV: You just saw {title} ⚽🔥",
        f"Why {title} is BROKEN 🤯"
    ]
    return " ".join(random.sample(tags, 6)), random.sample(hooks, 3)

# --- AI CORE (2026 Router URL) ---
def query_ai_deep(text):
    API_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-cnn"
    if "HF_TOKEN" not in st.secrets: return "AUTH_ERROR: TOKEN_MISSING"
    
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    payload = {
        "inputs": text[:1500],
        "parameters": {"max_length": 180, "min_length": 95, "repetition_penalty": 1.4}
    }
    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=15)
        res = r.json()
        return res[0]['summary_text'] if isinstance(res, list) else "CORE_LOADING... RETRY"
    except: return "SIGNAL_LOST"

# --- THE 20-SOURCE MATRIX ---
@st.cache_data(ttl=600)
def get_matrix_feed():
    sources = [
        "https://www.goal.com/en/feeds/news", "https://www.skysports.com/rss/12040",
        "https://www.theguardian.com/football/rss", "https://www.espn.com/espn/rss/soccer/news",
        "https://www.bbc.com/sport/football/rss.xml", "https://www.football365.com/news/feed",
        "https://feeds.feedburner.com/daily-express-football", "https://www.mirror.co.uk/sport/football/rss.xml",
        "https://www.football-espana.net/feed", "https://www.getfootballnewsfrance.com/feed",
        "https://www.getfootballnewsgermany.com/feed", "https://www.football-italia.net/feed",
        "https://worldsoccertalk.com/feed", "https://www.tribalfootball.com/rss.xml",
        "https://www.90min.com/posts.rss", "https://www.caughtoffside.com/feed",
        "https://www.standard.co.uk/sport/football/rss", "https://www.independent.co.uk/sport/football/rss",
        "https
