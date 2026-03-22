import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random

# --- CONFIG ---
st.set_page_config(page_title="Elite Soccer Hub", page_icon="⚽", layout="wide")

# --- 50+ SOURCE POOL ---
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
    ("Daily Sun", "https://www.snl24.com/dailysun/sport/rss"), ("The Athletic", "https://theathletic.com/rss"),
    ("Mirror Football", "https://www.mirror.co.uk/sport/football/rss.xml"), ("TalkSport", "https://talksport.com/football/feed/"),
    ("OneFootball", "https://onefootball.com/en/rss"), ("EuroSport", "https://www.eurosport.com/football/rss.xml"),
    ("Soccernet NG", "https://soccernet.ng/feed/"), ("Brila FM", "https://www.brila.net/feed/"),
    ("CAF Online", "https://www.cafonline.com/rss"), ("Barca Universal", "https://barcauniversal.com/feed/"),
    ("Juve FC", "https://www.juvefc.com/feed/"), ("This Is Anfield", "https://www.thisisanfield.com/feed/"),
    ("Daily Record", "https://www.dailyrecord.co.uk/sport/football/rss.xml"), ("Sowetan Live", "https://www.sowetanlive.co.za/sport/soccer/rss")
]

# --- SESSION & QUEUE LOGIC ---
if 'source_queue' not in st.session_state:
    all_sources = SOURCES.copy()
    random.shuffle(all_sources)
    st.session_state.source_queue = all_sources
    st.session_state.queue_index = 0

def fetch_next_20():
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
                r = requests.get(e.link, headers=headers, timeout=1.5)
                soup = BeautifulSoup(r.content, 'html.parser')
                img = soup.find("meta", property="og:image")
                img_url = img["content"] if img else "https://via.placeholder.com/400x220?text=Soccer+News"
                data.append({"s": name, "t": e.title, "l": e.link, "img": img_url})
        except: continue
    return data

def scrape_full_detail(url):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=3)
        soup = BeautifulSoup(r.content, 'html.parser')
        paras = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 100]
        return paras[0] if paras else "Full details available at the link."
    except: return "Details currently being updated..."

# --- UI DISPLAY ---
st.title("⚽ GLOBAL SOCCER HUB")
st.caption(f"Zero-Repeat Mode: Showing {st.session_state.queue_index}/{len(SOURCES)} sources in current cycle.")

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
                        <a href="{item['l']}" target="_blank" style="color: #00ff41; font-size: 11px; text-decoration: none;">🔗 Official Source</a>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            if st.button("🎤 Viral Generate", key=f"btn_{idx}", use_container_width=True):
                st.session_state.active = item

with s_col:
    st.markdown("### 🔥 Trending Social")
    trends = ["#Kane50", "Mbappe News", "Transfer Talk", "UCL Highlights", "Derby Day"]
    for t in trends:
        st.markdown(f'<div style="background:#111; padding:10px; border-radius:8px; margin-bottom:8px; border-left:3px solid #00ff41; font-size:14px;">{t}</div>', unsafe_allow_html=True)
    
    st.divider()
    if st.button("🔄 REFRESH: SHOW 20 NEW", use_container_width=True):
        st.session_state.visual_feed = fetch_next_20()
        st.rerun()

# --- THE DUAL-RESULT GENERATOR ---
if 'active' in st.session_state:
    it = st.session_state.active
    st.divider()
    with st.spinner("Analyzing current events..."):
        full_detail = scrape_full_detail(it['l'])
        tag_line = f"#{it['s'].replace(' ', '')} #SoccerNews #FootballUpdate #ViralSoccer"

        # 1. EASY & QUICK (The Viral Hook)
        easy_quick = (
            f"⚡ **FAST-ACTION UPDATE: {it['s'].upper()}** ⚡\n\n"
            f"📍 **STATUS:** {it['t']}\n\n"
            f"🚀 This is moving fast! Don't miss the details. 👇\n"
            f"🔗 {it['l']}\n\n"
            f"{tag_line}"
        )

        # 2. MORE DETAILED (The Deep Scoop)
        detailed_scoop = (
            f"📰 **DEEP SCOOP: {it['t'].upper()}**\n\n"
            f"🏆 **THE BREAKDOWN:** Reporting from **{it['s']}**, we've got major movement on the pitch. \n\n"
            f"⚽ **DETAILS:** {full_detail}\n\n"
            f"📈 **VERDICT:** This development is already sparking massive debate among fans. Is this the move of the year? 🤔\n\n"
            f"👇 **READ THE FULL OFFICIAL REPORT:**\n"
            f"{it['l']}\n\n"
            f"Drop your thoughts below! 👇 {tag_line}"
        )

        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("1️⃣ Easy & Quick Post")
            st.code(easy_quick, language="markdown")
        with col_b:
            st.subheader("2️⃣ Detailed Deep Scoop")
            st.code(detailed_scoop, language="markdown")
