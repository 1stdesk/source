import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random

# --- CONFIG ---
st.set_page_config(page_title="Ultra Soccer Scout 2026", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #050505; }
    .stButton>button { background-color: #00ff41; color: black; font-weight: bold; border-radius: 20px; }
    .news-card { 
        background-color: #121212; 
        padding: 20px; 
        border-radius: 15px; 
        border: 1px solid #333; 
        margin-bottom: 20px;
        transition: 0.3s;
    }
    .news-card:hover { border-color: #00ff41; }
    .source-tag { color: #00ff41; font-weight: bold; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; }
    .summary-box { 
        color: #d1d1d1; 
        font-size: 0.95rem; 
        background-color: #000000; 
        padding: 15px; 
        border-radius: 10px;
        margin-top: 10px;
        border-left: 3px solid #00ff41;
    }
    .headline-link { color: white; font-weight: bold; text-decoration: none; font-size: 1.2rem; line-height: 1.3; }
    </style>
    """, unsafe_allow_html=True)

# --- EXPANDED SOURCES FROM YOUR FILE ---
# I have converted your .txt list into usable RSS/Feed formats where available
MASTER_POOL = [
    ("Goal.com", "https://www.goal.com/en/feeds/news"),
    ("ESPN FC", "https://www.espn.com/espn/rss/soccer/news"),
    ("Sky Sports", "https://www.skysports.com/rss/12040"),
    ("BBC Sport", "https://push.api.bbci.co.uk/morph/items?page=1&limit=10&feed=football"),
    ("The Guardian", "https://www.theguardian.com/football/rss"),
    ("OneFootball", "https://onefootball.com/en/rss"),
    ("Yahoo Soccer", "https://sports.yahoo.com/soccer/rss/"),
    ("AS English", "https://en.as.com/rss/en/football/index.xml"),
    ("BeSoccer", "https://www.besoccer.com/rss"),
    ("Football365", "https://www.football365.com/feed"),
    ("Marca", "https://e00-marca.uecdn.es/rss/en/index.xml"),
    ("Mundo Deportivo", "https://www.mundodeportivo.com/rss/futbol"),
    ("Football Italia", "https://football-italia.net/feed/"),
    ("Kicker (DE)", "https://www.kicker.de/news.rss"),
    ("90min", "https://www.90min.com/posts.rss"),
    ("FourFourTwo", "https://www.fourfourtwo.com/feeds/all"),
    ("TEAMtalk", "https://www.teamtalk.com/feed"),
    ("CaughtOffside", "https://www.caughtoffside.com/feed/"),
    ("Soccer Laduma", "https://www.snl24.com/soccerladuma/rss"),
    ("KickOff", "https://www.snl24.com/kickoff/rss"),
    ("Ghana Soccernet", "https://ghanasoccernet.com/feed"),
    ("KingFut", "https://www.kingfut.com/feed/"),
    ("MLS Soccer", "https://www.mlssoccer.com/rss/news.xml"),
    ("Soccer America", "https://www.socceramerica.com/rss/headlines/"),
    ("101 Great Goals", "https://www.101greatgoals.com/feed/"),
    ("Football Talk", "https://www.footballtalk.org/feed/"),
    ("The Athletic", "https://theathletic.com/football/?rss=1"),
    ("Reuters Sports", "https://www.reuters.com/tools/rss/sport"),
    ("Calciomercato", "https://www.calciomercato.com/feed")
]

def scout_article(url):
    """Deep scan for image and text summary."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=7)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Image Search
        img = None
        og_img = soup.find("meta", property="og:image")
        if og_img:
            img = og_img["content"]
        
        # Summary Search (Top 2-3 detailed paragraphs)
        paras = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 100]
        summary = " ".join(paras[:2])
        
        return {"img": img, "text": summary if summary else "No summary available for this source."}
    except:
        return None

def get_20_random():
    shuffled = list(MASTER_POOL)
    random.shuffle(shuffled)
    selection = []
    for name, url in shuffled:
        if len(selection) >= 20: break
        try:
            f = feedparser.parse(url)
            if f.entries:
                entry = f.entries[0]
                selection.append({'s': name, 't': entry.title, 'l': entry.link})
        except: continue
    return selection

# --- UI ---
st.title("⚽ ULTRA SOCCER SCOUT")
st.caption(f"Scanning {len(MASTER_POOL)} Global Sources")

if st.button("🔄 GENERATE NEW 20-SOURCE FEED"):
    st.session_state.ultra_feed = get_20_random()

if 'ultra_feed' not in st.session_state:
    st.session_state.ultra_feed = get_20_random()

# Display
for i, item in enumerate(st.session_state.ultra_feed, 1):
    st.markdown(f'<div class="news-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="source-tag">{i}. {item["s"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<a href="{item["l"]}" target="_blank" class="headline-link">{item["t"]}</a>', unsafe_allow_html=True)
    
    if st.button(f"🧠 AI SCOUT REPORT #{i}", key=f"btn_{i}"):
        with st.spinner("Analyzing..."):
            data = scout_article(item['l'])
            if data:
                c1, c2 = st.columns([1, 2])
                with c1:
                    if data['img']:
                        st.image(data['img'], use_container_width=True)
                        img_bytes = requests.get(data['img']).content
                        st.download_button("💾 Download Image", img_bytes, f"soccer_{i}.jpg", "image/jpeg")
                with c2:
                    st.markdown(f'<div class="summary-box"><b>QUICK SCOUT:</b><br>{data["text"]}</div>', unsafe_allow_html=True)
            else:
                st.warning("Could not extract data from this source.")
    st.markdown('</div>', unsafe_allow_html=True)
