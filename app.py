import streamlit as st
import requests
import feedparser
import hashlib
from bs4 import BeautifulSoup
import time
import random

# --- FUTURISTIC UI CONFIG ---
st.set_page_config(page_title="NEO-SCOUT // 20_SOURCE_MATRIX", page_icon="🛰️", layout="wide")

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
    .title-suggestion { color: #ff00ff !important; font-style: italic; font-weight: bold; margin: 5px 0; }
    </style>
    """, unsafe_allow_html=True)

# --- VIRAL ENGINE (Titles & Tags) ---
def generate_viral_content(title):
    # Hashtags
    tags = ["#SportsTok", "#FootballNews", "#SoccerDaily", "#GameChanger", "#NewHeights", "#PatMcAfeeShow", "#ESPNPlus", "#ViralSports"]
    
    # Video Title Suggestions (TikTok/FB Style)
    templates = [
        f"🚨 BIG REVEAL: {title} 😱",
        f"The TRUTH about {title}... 🤫",
        f"POV: You just heard {title} ⚽🔥",
        f"Why NO ONE is talking about {title} 🤯",
        f"EVERYTHING changed for {title} today! 📉"
    ]
    
    return " ".join(random.sample(tags, 6)), random.sample
