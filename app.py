import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random

# --- CONFIG ---
st.set_page_config(page_title="Elite Soccer Hub", page_icon="⚽", layout="wide")

# --- TRENDING TOPICS (Mock Social Data for March 2026) ---
TRENDS = [
    {"topic": "#SunderlandStunNewcastle", "count": "1.2M posts", "source": "X/Twitter"},
    {"topic": "Neymar Selection Controversy", "count": "850K views", "source": "TikTok"},
    {"topic": "Harry Kane 50 UCL Goals", "count": "Hot", "source": "Reddit r/soccer"},
    {"topic": "Como Serie A CL Spot", "count": "Trending", "source": "Instagram"},
    {"topic": "#WorldCup2026Kits", "count": "200K shares", "source": "X/Twitter"},
    {"topic": "Marcus Rashford to Barca?", "count": "Viral", "source": "TransferTalk"}
]

# --- SOURCE POOL ---
BIG_POOL = [
    ("Goal.com", "https://www.goal.com/en/feeds/news"), ("Sky Sports", "https://www.skysports.com/rss/12040"),
    ("BBC Sport", "http://newsrss.bbc.co.uk/rss/sportonline_uk_edition/football/rss.xml"), ("Transfermarkt", "https://www.transfermarkt.com/rss/news"),
    ("ESPN FC", "https://www.espn.com/espn/rss/soccer/news"), ("The Guardian", "https://www.theguardian.com/football/rss"),
    ("Marca", "https://e00-marca.uecdn.es/rss/en/index.xml"), ("Football Italia", "https://football-italia.net/feed/"),
    ("The Athletic", "https://theathletic.com/rss"), ("Mirror Football", "https://www.mirror.co.uk/sport/football/rss.xml")
]

def get_new_batch():
    selected = random.sample(BIG_POOL, 8) # Show 8 for clarity in this layout
    data = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    for name, url in selected:
        try:
            f = feedparser.parse(url)
            if f.entries:
                e = f.entries[0]
                r = requests.get(e.link, headers=headers, timeout=2)
                soup = BeautifulSoup(r.content, 'html.parser')
                img = soup.find("meta", property="og:image")
                img_url = img["content"] if img else "https://via.placeholder.com/400x200"
                data.append({"s": name, "t": e.title, "l": e.link, "img": img_url})
        except: continue
    return data

# --- UI LAYOUT ---
st.title("⚽ GLOBAL SOCCER HUB")

# Create Main Content and Sidebar
main_col, side_col = st.columns([3, 1])

with main_col:
    if 'visual_feed' not in st.session_state:
        st.session_state.visual_feed = get_new_batch()

    # 2x4 Grid for Main Content
    grid_cols = st.columns(2)
    for idx, item in enumerate(st.session_state.visual_feed):
        with grid_cols[idx % 2]:
            st.markdown(f'''
                <div style="background-color: rgb(17, 17, 17); border-radius: 12px; border: 1px solid rgb(51, 51, 51); margin-bottom: 20px; overflow: hidden;">
                    <img src="{item['img']}" style="width: 100%; height: 220px; object-fit: cover;">
                    <div style="padding: 15px;">
                        <span style="color: #00ff41; font-size: 10px; font-weight: bold;">{item['s'].upper()}</span>
                        <h4 style="color: white; margin-top: 5px; font-size: 16px;">{item['t']}</h4>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            if st.button("Generate Post", key=f"btn_{idx}", use_container_width=True):
                st.session_state.active = item

with side_col:
    st.markdown("### 🔥 Trending Now")
    for t in TRENDS:
        st.markdown(f'''
            <div style="background-color: #111; padding: 12px; border-radius: 8px; border-left: 4px solid #00ff41; margin-bottom: 10px;">
                <p style="font-size: 12px; color: #888; margin: 0;">{t['source']}</p>
                <p style="font-weight: bold; color: white; margin: 0;">{t['topic']}</p>
                <p style="font-size: 11px; color: #00ff41; margin: 0;">{t['count']}</p>
            </div>
        ''', unsafe_allow_html=True)
    
    if st.button("🔄 Refresh All", use_container_width=True):
        st.session_state.visual_feed = get_new_batch()
        st.rerun()

# POST GENERATION (Bottom Section)
if 'active' in st.session_state:
    it = st.session_state.active
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.code(f"📰 DEEP SCOOP: {it['t'].upper()}\n\n🔗 Source: {it['l']}", language="markdown")
    with c2:
        st.code(f"⚡ FAST UPDATE\n\n📍 {it['t']}\n\n#Soccer #Trending", language="markdown")
