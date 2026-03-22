import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random

# --- CONFIG ---
st.set_page_config(page_title="Elite Soccer Hub", page_icon="⚽", layout="wide")

# --- MOCK SOCIAL TRENDS (March 2026) ---
TRENDS = [
    {"topic": "#SunderlandStunNewcastle", "count": "1.2M posts", "source": "X/Twitter"},
    {"topic": "Neymar Selection Controversy", "count": "850K views", "source": "TikTok"},
    {"topic": "Harry Kane 50 UCL Goals", "count": "Hot", "source": "Reddit r/soccer"},
    {"topic": "Como Serie A CL Spot", "count": "Trending", "source": "Instagram"},
    {"topic": "#WorldCup2026Kits", "count": "200K shares", "source": "X/Twitter"}
]

# --- 50+ SOURCE POOL ---
BIG_POOL = [
    ("Goal.com", "https://www.goal.com/en/feeds/news"), ("Sky Sports", "https://www.skysports.com/rss/12040"),
    ("BBC Sport", "http://newsrss.bbc.co.uk/rss/sportonline_uk_edition/football/rss.xml"), ("Soccer Laduma", "https://www.snl24.com/soccerladuma/rss"),
    ("Transfermarkt", "https://www.transfermarkt.com/rss/news"), ("ESPN FC", "https://www.espn.com/espn/rss/soccer/news"),
    ("The Guardian", "https://www.theguardian.com/football/rss"), ("90min", "https://www.90min.com/posts.rss"),
    ("Marca", "https://e00-marca.uecdn.es/rss/en/index.xml"), ("AS English", "https://en.as.com/rss/en/football/index.xml"),
    ("Football Italia", "https://football-italia.net/feed/"), ("Daily Mail", "https://www.dailymail.co.uk/sport/football/index.rss"),
    ("KickOff", "https://www.snl24.com/kickoff/rss"), ("Sowetan Live", "https://www.sowetanlive.co.za/sport/soccer/rss"),
    ("Ghana Soccernet", "https://ghanasoccernet.com/feed"), ("CaughtOffside", "https://www.caughtoffside.com/feed/"),
    ("TEAMtalk", "https://www.teamtalk.com/feed"), ("World Soccer", "https://www.worldsoccer.com/feed"),
    ("FourFourTwo", "https://www.fourfourtwo.com/rss.xml"), ("Daily Sun", "https://www.snl24.com/dailysun/sport/rss"),
    ("The Athletic", "https://theathletic.com/rss"), ("Mirror Football", "https://www.mirror.co.uk/sport/football/rss.xml"),
    ("TalkSport", "https://talksport.com/football/feed/"), ("OneFootball", "https://onefootball.com/en/rss"),
    ("EuroSport", "https://www.eurosport.com/football/rss.xml")
]

def get_new_batch():
    current_names = [item['s'] for item in st.session_state.get('visual_feed', [])]
    available_pool = [s for s in BIG_POOL if s[0] not in current_names]
    if len(available_pool) < 20: available_pool = BIG_POOL
    selected = random.sample(available_pool, 20)
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
st.title("⚽ GLOBAL NEWSROOM & SOCIAL PULSE")

main_col, side_col = st.columns([3.5, 1])

with main_col:
    if 'visual_feed' not in st.session_state:
        st.session_state.visual_feed = get_new_batch()

    # 4-Column Responsive Grid
    grid_cols = st.columns(4)
    for idx, item in enumerate(st.session_state.visual_feed):
        with grid_cols[idx % 4]:
            st.markdown(f'''
                <div style="background-color: #111; border-radius: 10px; border: 1px solid #333; margin-bottom: 15px; overflow: hidden; height: 380px;">
                    <img src="{item['img']}" style="width: 100%; height: 180px; object-fit: cover;">
                    <div style="padding: 10px;">
                        <p style="color: #00ff41; font-size: 11px; font-weight: bold; margin: 0;">{item['s'].upper()}</p>
                        <p style="font-size: 14px; font-weight: bold; color: white; margin-top: 5px; height: 50px; overflow: hidden;">{item['t']}</p>
                        <a href="{item['l']}" target="_blank" style="color: #888; font-size: 12px; text-decoration: none;">🔗 Read Source</a>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            if st.button("Generate Post", key=f"btn_{idx}", use_container_width=True):
                st.session_state.active = item

with side_col:
    st.markdown("### 🔥 Trending on Social")
    for t in TRENDS:
        st.markdown(f'''
            <div style="background-color: #111; padding: 12px; border-radius: 8px; border-left: 4px solid #00ff41; margin-bottom: 10px;">
                <p style="font-size: 11px; color: #888; margin: 0;">{t['source']}</p>
                <p style="font-weight: bold; color: white; margin: 0; font-size: 14px;">{t['topic']}</p>
                <p style="font-size: 11px; color: #00ff41; margin: 0;">{t['count']}</p>
            </div>
        ''', unsafe_allow_html=True)
    
    st.divider()
    if st.button("🔄 REFRESH ALL SOURCES", use_container_width=True):
        st.session_state.visual_feed = get_new_batch()
        st.rerun()

# --- POST GENERATION (DIRECT & CLICKABLE) ---
if 'active' in st.session_state:
    it = st.session_state.active
    st.divider()
    st.subheader(f"Generated Content for: {it['t']}")
    
    tag_line = f"#{it['s'].replace(' ', '')} #Football2026 #SoccerNews"
    
    deep_post = f"📰 **THE DEEP SCOOP**\n\n⚽ {it['t']}\n\n🔗 **READ FULL STORY:** {it['l']}\n\n{tag_line}"
    fast_post = f"⚡ **FAST UPDATE**\n\n📍 {it['t']}\n\n👉 Full details here: {it['l']}\n\n{tag_line}"

    col_left, col_right = st.columns(2)
    with col_left:
        st.markdown("#### Option 1: Detailed")
        st.code(deep_post, language="markdown")
        st.link_button("Go to Official Source", it['l'])
    with col_right:
        st.markdown("#### Option 2: Short")
        st.code(fast_post, language="markdown")
        st.link_button("Share Source Link", it['l'])
