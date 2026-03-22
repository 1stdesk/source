import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random

# --- CONFIG ---
st.set_page_config(page_title="Randomized Soccer Hub", page_icon="⚽", layout="wide")

# --- SOURCE POOLS ---
# Original 20
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

# New "Random" Backup Sources
RESERVE_POOL = [
    ("The Athletic", "https://theathletic.com/rss"),
    ("Mirror Football", "https://www.mirror.co.uk/sport/football/rss.xml"),
    ("The Sun Football", "https://www.thesun.co.uk/sport/football/feed/"),
    ("Liverpool Echo", "https://www.liverpoolecho.co.uk/sport/football/rss.xml"),
    ("Manchester Evening News", "https://www.manchestereveningnews.co.uk/sport/football/rss.xml"),
    ("TalkSport", "https://talksport.com/football/feed/"),
    ("OneFootball", "https://onefootball.com/en/rss"),
    ("Football.London", "https://www.football.london/rss.xml"),
    ("EuroSport", "https://www.eurosport.com/football/rss.xml"),
    ("Sporting News", "https://www.sportingnews.com/us/rss/soccer")
]

ALL_SOURCES = MASTER_POOL + RESERVE_POOL

# --- CORE FUNCTIONS ---
def get_random_20():
    """Shuffles the entire list and picks 20 random sources."""
    selected = random.sample(ALL_SOURCES, 20)
    data = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    for name, url in selected:
        try:
            f = feedparser.parse(url)
            if f.entries:
                e = f.entries[0]
                # Thumbnail extraction
                r = requests.get(e.link, headers=headers, timeout=3)
                soup = BeautifulSoup(r.content, 'html.parser')
                img = soup.find("meta", property="og:image")
                img_url = img["content"] if img else "https://via.placeholder.com/400x225?text=Soccer"
                data.append({"s": name, "t": e.title, "l": e.link, "img": img_url})
        except: continue
    return data

# --- UI ---
st.title("⚽ RANDOMIZED GLOBAL NEWSROOM")
st.subheader("Click 'Refresh' to cycle through 30+ different world sources")

if 'visual_feed' not in st.session_state:
    st.session_state.visual_feed = get_random_20()

# GRID DISPLAY
cols = st.columns(4)
for idx, item in enumerate(st.session_state.visual_feed):
    with cols[idx % 4]:
        st.markdown(f'''
            <div style="background-color:#111; padding:10px; border-radius:10px; border:1px solid #333; height:380px;">
                <img src="{item['img']}" style="width:100%; height:150px; object-fit:cover; border-radius:5px;">
                <p style="color:#00ff41; font-weight:bold; font-size:12px; margin-top:5px;">{item['s']}</p>
                <p style="font-size:14px; height:60px; overflow:hidden;">{item['t']}</p>
            </div>
        ''', unsafe_allow_html=True)
        if st.button("Generate Post", key=f"btn_{idx}"):
            st.session_state.active = item

# POST GENERATION
if 'active' in st.session_state:
    it = st.session_state.active
    st.divider()
    tag_line = f"#{it['s'].replace(' ', '')} #Soccer #Update2026"
    
    deep_text = f"📰 **THE DEEP SCOOP: {it['t'].upper()}**\n\n⚽ {it['t']}\n\n🔗 **FULL STORY:** {it['l']}\n\n{tag_line}"
    fast_text = f"⚡ **FAST UPDATE**\n\n📍 {it['t']}\n\n👉 Details: {it['l']}\n\n{tag_line}"

    c1, c2 = st.columns(2)
    with c1: st.code(deep_text, language="markdown")
    with c2: st.code(fast_text, language="markdown")

# REFRESH BUTTON (Shuffles the deck)
if st.button("🔄 REFRESH & RANDOMIZE SOURCES"):
    st.session_state.visual_feed = get_random_20()
    st.rerun()
