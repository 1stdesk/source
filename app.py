import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import re

# --- CONFIG ---
st.set_page_config(page_title="Soccer Scout Simple", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #050505; color: white; }
    .stCode { background-color: #111 !important; border: 1px solid #00ff41 !important; color: #e0e0e0 !important; }
    .news-card {
        background-color: #111; border: 1px solid #333; border-radius: 10px;
        padding: 10px; height: 380px; transition: 0.3s;
    }
    .news-card:hover { border-color: #00ff41; }
    </style>
    """, unsafe_allow_html=True)

# --- THE 20 SOURCES ---
MASTER_POOL = [
    ("Goal.com", "https://www.goal.com/en/feeds/news"),
    ("Sky Sports", "https://www.skysports.com/rss/12040"),
    ("BBC Sport", "http://newsrss.bbc.co.uk/rss/sportonline_uk_edition/football/rss.xml"),
    ("Soccer Laduma", "https://www.snl24.com/soccerladuma/rss"),
    ("Transfermarkt", "https://www.transfermarkt.com/rss/news"),
    ("ESPN FC", "https://www.espn.com/espn/rss/soccer/news"),
    ("The Guardian", "https://www.theguardian.com/football/rss"),
    ("90min", "https://www.90min.com/posts.rss"),
    ("Marca", "https://e00-marca.uecdn.es/rss/en/index.xml"),
    ("AS English", "https://en.as.com/rss/en/football/index.xml"),
    ("Football Italia", "https://football-italia.net/feed/"),
    ("Daily Mail", "https://www.dailymail.co.uk/sport/football/index.rss"),
    ("KickOff", "https://www.snl24.com/kickoff/rss"),
    ("Sowetan Live", "https://www.sowetanlive.co.za/sport/soccer/rss"),
    ("Ghana Soccernet", "https://ghanasoccernet.com/feed"),
    ("CaughtOffside", "https://www.caughtoffside.com/feed/"),
    ("TEAMtalk", "https://www.teamtalk.com/feed"),
    ("World Soccer", "https://www.worldsoccer.com/feed"),
    ("FourFourTwo", "https://www.fourfourtwo.com/rss.xml"),
    ("Daily Sun Soccer", "https://www.snl24.com/dailysun/sport/rss")
]

@st.cache_data(ttl=600)
def fetch_grid():
    data = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    for name, url in MASTER_POOL:
        try:
            f = feedparser.parse(url)
            if f.entries:
                e = f.entries[0]
                r = requests.get(e.link, headers=headers, timeout=3)
                soup = BeautifulSoup(r.content, 'html.parser')
                img = soup.find("meta", property="og:image")
                img_url = img["content"] if img else "https://via.placeholder.com/400x225?text=Soccer"
                data.append({"s": name, "t": e.title, "l": e.link, "img": img_url})
        except: continue
    return data

def quick_scrape(url):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        soup = BeautifulSoup(r.content, 'html.parser')
        paras = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 100]
        return paras[0] if paras else "Full story details at the link."
    except: return "Summary unavailable."

# --- UI DISPLAY ---
st.title("⚽ 20-Source Newsroom")

if 'visual_feed' not in st.session_state:
    st.session_state.visual_feed = fetch_grid()

cols = st.columns(4)
for idx, item in enumerate(st.session_state.visual_feed):
    with cols[idx % 4]:
        st.markdown(f'''
            <div class="news-card">
                <img src="{item['img']}" style="width:100%; height:160px; object-fit:cover; border-radius:5px;">
                <p style="color:#00ff41; font-size:12px; margin:10px 0 0 0;">{item['s']}</p>
                <p style="font-weight:bold; font-size:14px;">{item['t']}</p>
            </div>
        ''', unsafe_allow_html=True)
        if st.button("Generate Post", key=f"btn_{idx}"):
            st.session_state.active = item

st.divider()

# --- THE SIMPLIFIED SUMMARY OUTPUT ---
if 'active' in st.session_state:
    it = st.session_state.active
    with st.spinner("Simplifying summary..."):
        detail = quick_scrape(it['l'])
        # Automatic Hashtags based on source and topic
        tag_line = f"#{it['s'].replace(' ', '')} #Football #SoccerNews #Update2026"
        
        # 1. THE DEEP SCOOP
        deep_text = (
            f"📰 **THE DEEP SCOOP: {it['t'].upper()}**\n\n"
            f"⚽ **DETAILS:** {detail}\n\n"
            f"🔗 **FULL STORY:** {it['l']}\n\n"
            f"{tag_line}"
        )

        # 2. THE FAST UPDATE
        fast_text = (
            f"⚡ **FAST UPDATE**\n\n"
            f"📍 {it['t']}\n\n"
            f"👉 Details: {it['l']}\n\n"
            f"{tag_line}"
        )

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Option 1: Detailed Post")
            st.code(deep_text, language="markdown")
        with c2:
            st.subheader("Option 2: Short Post")
            st.code(fast_text, language="markdown")

if st.button("🔄 Refresh Grid"):
    st.cache_data.clear()
    del st.session_state.visual_feed
    st.rerun()
