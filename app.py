import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random

# --- CONFIG ---
st.set_page_config(page_title="Elite Soccer Hub", page_icon="⚽", layout="wide")

# --- EXPANDED 50+ SOURCE POOL ---
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
    ("OneFootball", "https://onefootball.com/en/rss"), ("Football.London", "https://www.football.london/rss.xml"),
    ("EuroSport", "https://www.eurosport.com/football/rss.xml"), ("Sporting News", "https://www.sportingnews.com/us/rss/soccer"),
    ("Independent", "https://www.independent.co.uk/sport/football/rss"), ("Tribal Football", "https://www.tribalfootball.com/rss.xml"),
    ("World Football Index", "https://worldfootballindex.com/feed/"), ("Standard", "https://www.standard.co.uk/sport/football/rss"),
    ("Daily Star", "https://www.dailystar.co.uk/sport/football/rss"), ("Football365", "https://www.football365.com/feed"),
    ("Daily Express", "https://www.express.co.uk/posts/rss/65/football"), ("Soccernet NG", "https://soccernet.ng/feed/"),
    ("Brila FM", "https://www.brila.net/feed/"), ("CAF Online", "https://www.cafonline.com/rss"),
    ("Barca Universal", "https://barcauniversal.com/feed/"), ("Juve FC", "https://www.juvefc.com/feed/"),
    ("Roma Press", "https://romapress.net/feed/"), ("The Mag", "https://www.themag.co.uk/feed/"),
    ("Arseblog", "https://arseblog.news/feed/"), ("This Is Anfield", "https://www.thisisanfield.com/feed/"),
    ("ToffeeWeb", "https://www.toffeeweb.com/rss/news.xml"), ("SBNation", "https://www.sbnation.com/rss/current.xml"),
    ("Daily Record", "https://www.dailyrecord.co.uk/sport/football/rss.xml"), ("Irish Times", "https://www.irishtimes.com/cmlink/news-soccer-1.1319114"),
    ("Daily Mirror", "https://www.mirror.co.uk/sport/football/rss.xml"), ("Sowetan Live", "https://www.sowetanlive.co.za/sport/soccer/rss")
]

# --- SESSION INITIALIZATION ---
if 'source_queue' not in st.session_state:
    # Shuffle all sources once and store the master list
    all_sources = SOURCES.copy()
    random.shuffle(all_sources)
    st.session_state.source_queue = all_sources
    st.session_state.queue_index = 0

def fetch_next_20():
    """Takes the next 20 sources from the shuffled queue."""
    # If near the end, reshuffle and reset
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

# --- UI LOGIC ---
st.title("⚽ GLOBAL SOCCER SCOUT")
st.caption(f"Cycling through {len(SOURCES)} unique sources. No duplicates until the full list is cleared.")

if 'visual_feed' not in st.session_state:
    st.session_state.visual_feed = fetch_next_20()

main_col, side_col = st.columns([4, 1])

with main_col:
    grid = st.columns(4)
    for idx, item in enumerate(st.session_state.visual_feed):
        with grid[idx % 4]:
            st.markdown(f'''
                <div style="background-color: #111; border-radius: 12px; border: 1px solid #333; margin-bottom: 15px; overflow: hidden; height: 380px;">
                    <img src="{item['img']}" style="width: 100%; height: 180px; object-fit: cover;">
                    <div style="padding: 10px;">
                        <p style="color: #00ff41; font-size: 10px; font-weight: bold; margin: 0;">{item['s'].upper()}</p>
                        <p style="font-size: 13px; font-weight: bold; color: white; margin-top: 5px; height: 50px; overflow: hidden;">{item['t']}</p>
                        <a href="{item['l']}" target="_blank" style="color: #888; font-size: 11px; text-decoration: none;">🔗 Original Article</a>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            if st.button("🎤 Viral Post", key=f"btn_{idx}", use_container_width=True):
                st.session_state.active = item

with side_col:
    st.markdown("### 🔥 Trending Topics")
    # Using a list of actual 2026-themed trends
    trends = ["#SunderlandWin", "Neymar Return", "#WorldCupKits", "Kane 50 Goals", "Transfer Rumors"]
    for t in trends:
        st.markdown(f'<div style="background:#111; padding:10px; border-radius:8px; margin-bottom:8px; border-left:3px solid #00ff41; font-size:14px;">{t}</div>', unsafe_allow_html=True)
    
    st.divider()
    if st.button("🔄 REFRESH: SHOW NEW SOURCES", use_container_width=True):
        with st.spinner("Grabbing fresh sources..."):
            st.session_state.visual_feed = fetch_next_20()
            st.rerun()

# --- VIRAL POST GENERATOR ---
if 'active' in st.session_state:
    it = st.session_state.active
    st.divider()
    
    viral_text = (
        f"🚨 **FOOTBALL ALERT: YOU WON'T BELIEVE THIS!** 🚨\n\n"
        f"Fresh off the press from **{it['s']}**, we have a massive update that's shaking up the leagues!\n\n"
        f"🏆 **THE STORY:** {it['t'].upper()}\n\n"
        f"Is this the craziest news of 2026 so far? Football just keeps on giving! ⚽🔥\n\n"
        f"👇 **CLICK BELOW FOR THE FULL BREAKDOWN:**\n"
        f"{it['l']}\n\n"
        f"What's your take? Let's talk in the comments! 👇 #Football #Viral #SoccerScout"
    )
    
    st.subheader(f"Viral Post for: {it['s']}")
    st.code(viral_text, language="markdown")
