import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Elite Soccer Hub: Insider Edition", page_icon="⚽", layout="wide")

# --- 2. THE 50+ SOURCE POOL ---
SOURCES = [
    ("Goal.com", "https://www.goal.com/en/feeds/news"), ("Sky Sports", "https://www.skysports.com/rss/12040"),
    ("BBC Sport", "http://newsrss.bbc.co.uk/rss/sportonline_uk_edition/football/rss.xml"), ("Transfermarkt", "https://www.transfermarkt.com/rss/news"),
    ("ESPN FC", "https://www.espn.com/espn/rss/soccer/news"), ("The Guardian", "https://www.theguardian.com/football/rss"),
    ("90min", "https://www.90min.com/posts.rss"), ("Marca", "https://e00-marca.uecdn.es/rss/en/index.xml"),
    ("AS English", "https://en.as.com/rss/en/football/index.xml"), ("Football Italia", "https://football-italia.net/feed/"),
    ("Daily Mail", "https://www.dailymail.co.uk/sport/football/index.rss"), ("KickOff", "https://www.snl24.com/kickoff/rss"),
    ("Soccer Laduma", "https://www.snl24.com/soccerladuma/rss"), ("Ghana Soccernet", "https://ghanasoccernet.com/feed"),
    ("CaughtOffside", "https://www.caughtoffside.com/feed/"), ("TEAMtalk", "https://www.teamtalk.com/feed"),
    ("World Soccer", "https://www.worldsoccer.com/feed"), ("FourFourTwo", "https://www.fourfourtwo.com/rss.xml"),
    ("The Athletic", "https://theathletic.com/rss"), ("Mirror Football", "https://www.mirror.co.uk/sport/football/rss.xml"),
    ("TalkSport", "https://talksport.com/football/feed/"), ("OneFootball", "https://onefootball.com/en/rss"),
    ("Soccernet NG", "https://soccernet.ng/feed/"), ("Brila FM", "https://www.brila.net/feed/"),
    ("Barca Universal", "https://barcauniversal.com/feed/"), ("This Is Anfield", "https://www.thisisanfield.com/feed/"),
    ("Daily Record", "https://www.dailyrecord.co.uk/sport/football/rss.xml")
]

# --- 3. QUEUE SYSTEM (ZERO-REPEAT LOGIC) ---
if 'source_queue' not in st.session_state:
    all_sources = SOURCES.copy()
    random.shuffle(all_sources)
    st.session_state.source_queue = all_sources
    st.session_state.queue_index = 0

def fetch_next_20():
    # If we hit the end of the 50 sources, reshuffle and restart
    if st.session_state.queue_index + 20 > len(st.session_state.source_queue):
        random.shuffle(st.session_state.source_queue)
        st.session_state.queue_index = 0
    
    selected = st.session_state.source_queue[st.session_state.queue_index : st.session_state.queue_index + 20]
    st.session_state.queue_index += 20
    
    data = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    for name, url in selected:
        try:
            f = feedparser.parse(url)
            if f.entries:
                e = f.entries[0]
                # Extract Thumbnail
                r = requests.get(e.link, headers=headers, timeout=1.5)
                soup = BeautifulSoup(r.content, 'html.parser')
                img = soup.find("meta", property="og:image")
                img_url = img["content"] if img else "https://via.placeholder.com/400x225?text=Soccer+Update"
                data.append({"s": name, "t": e.title, "l": e.link, "img": img_url})
        except: continue
    return data

def scrape_full_detail(url):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=3)
        soup = BeautifulSoup(r.content, 'html.parser')
        paras = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 100]
        return paras[0] if paras else "Full tactical details available at the link."
    except: return "Details currently being verified by our newsroom..."

# --- 4. MAIN INTERFACE ---
st.title("⚽ GLOBAL NEWSROOM: INSIDER MODE")

if 'visual_feed' not in st.session_state:
    st.session_state.visual_feed = fetch_next_20()

m_col, s_col = st.columns([4, 1.2])

with m_col:
    grid = st.columns(4)
    for idx, item in enumerate(st.session_state.visual_feed):
        with grid[idx % 4]:
            st.markdown(f'''
                <div style="background-color: #111; border-radius: 12px; border: 1px solid #333; margin-bottom: 15px; overflow: hidden; height: 380px;">
                    <img src="{item['img']}" style="width: 100%; height: 180px; object-fit: cover;">
                    <div style="padding: 10px;">
                        <p style="color: #00ff41; font-size: 10px; font-weight: bold; margin: 0;">{item['s'].upper()}</p>
                        <p style="font-size: 13px; font-weight: bold; color: white; margin-top: 5px; height: 55px; overflow: hidden;">{item['t']}</p>
                        <a href="{item['l']}" target="_blank" style="color: #00ff41; font-size: 11px; text-decoration: none; font-weight: bold;">🔗 OPEN SOURCE</a>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            if st.button("🎤 FABRIZIO STYLE", key=f"btn_{idx}", use_container_width=True):
                st.session_state.active = item

with s_col:
    st.markdown("### 🔥 Trending Topics")
    trends = ["#HereWeGo", "#TransferDeadline", "#UCLDraw", "#BallonDor", "#EPLUpdates"]
    for t in trends:
        st.markdown(f'<div style="background:#111; padding:10px; border-radius:8px; margin-bottom:8px; border-left:3px solid #00ff41; font-size:14px; color: white;">{t}</div>', unsafe_allow_html=True)
    
    st.divider()
    if st.button("🔄 REFRESH: 20 NEW SOURCES", use_container_width=True):
        st.session_state.visual_feed = fetch_next_20()
        st.rerun()

# --- 5. THE GENERATOR (FABRIZIO ENERGY) ---
if 'active' in st.session_state:
    it = st.session_state.active
    st.divider()
    with st.spinner("Decoding tactical radiography..."):
        full_detail = scrape_full_detail(it['l'])
        tag_line = f"#{it['s'].replace(' ', '')} #FootballNews #HereWeGo #SoccerUpdate #Transfers"

        # OPTION 1: EASY & QUICK
        easy_quick = (
            f"⚡ **FAST-ACTION UPDATE: {it['s'].upper()}** ⚡\n\n"
            f"📍 **STATUS:** {it['t']}\n\n"
            f"🚀 This is moving fast! Don't miss the details. 👇\n"
            f"🔗 {it['l']}\n\n"
            f"{tag_line}"
        )

        # OPTION 2: INSIDER DEEP SCOOP (The Fabrizio Style)
        detailed_scoop = (
            f"📰 **THE DEEP SCOOP: THE {it['s'].upper()} DOMINO EFFECT**\n"
            f"**\"HERE WE GO\" ENERGY — UNDERSTANDING THE STRATEGY**\n\n"
            f"🏆 **THE BREAKDOWN:**\n"
            f"Reporting via **{it['s']}**, we are witnessing a high-stakes chess match. The club isn't just making a move; they are shifting the entire market landscape with this development.\n\n"
            f"⚽ **INSIDER CONTEXT:**\n"
            f"{full_detail}\n\n"
            f"📈 **MARKET VERDICT:**\n"
            f"This isn't just news; it's a statement of intent. Analysts suggest this move is designed to bypass financial constraints while securing elite-level talent. Is this a masterstroke? 🤔\n\n"
            f"👇 **FULL TACTICAL RADIOGRAPHY HERE:**\n"
            f"{it['l']}\n\n"
            f"Drop your thoughts! 👇 {tag_line}"
        )

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("1️⃣ Viral Hook (Easy)")
            st.code(easy_quick, language="markdown")
        with c2:
            st.subheader("2️⃣ Insider Scoop (Detailed)")
            st.code(detailed_scoop, language="markdown")
