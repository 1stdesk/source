import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random

# --- CONFIG ---
st.set_page_config(page_title="Infinite Soccer Scout", page_icon="⚽", layout="wide")

# --- MASSIVE SOURCE POOL (50+ Sources) ---
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
    ("Football.London", "https://www.football.london/rss.xml"), ("EuroSport", "https://www.eurosport.com/football/rss.xml"),
    ("Sporting News", "https://www.sportingnews.com/us/rss/soccer"), ("Independent", "https://www.independent.co.uk/sport/football/rss"),
    ("Tribal Football", "https://www.tribalfootball.com/rss.xml"), ("World Football Index", "https://worldfootballindex.com/feed/"),
    ("Standard", "https://www.standard.co.uk/sport/football/rss"), ("Daily Star", "https://www.dailystar.co.uk/sport/football/rss"),
    ("Football365", "https://www.football365.com/feed"), ("Daily Express", "https://www.express.co.uk/posts/rss/65/football"),
    ("Soccernet NG", "https://soccernet.ng/feed/"), ("Brila FM", "https://www.brila.net/feed/"),
    ("CAF Online", "https://www.cafonline.com/rss"), ("Barca Universal", "https://barcauniversal.com/feed/"),
    ("Juve FC", "https://www.juvefc.com/feed/"), ("Roma Press", "https://romapress.net/feed/"),
    ("The Mag", "https://www.themag.co.uk/feed/"), ("Arseblog", "https://arseblog.news/feed/"),
    ("This Is Anfield", "https://www.thisisanfield.com/feed/"), ("ToffeeWeb", "https://www.toffeeweb.com/rss/news.xml"),
    ("Daily Record", "https://www.dailyrecord.co.uk/sport/football/rss.xml")
]

def get_new_batch():
    """Picks 20 sources that are NOT currently shown to ensure variety."""
    current_names = [item['s'] for item in st.session_state.get('visual_feed', [])]
    available_pool = [s for s in BIG_POOL if s[0] not in current_names]
    
    # Reset if we've cycled through almost everything
    if len(available_pool) < 20:
        available_pool = BIG_POOL

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
                img_url = img["content"] if img else "https://via.placeholder.com/400x225?text=Soccer"
                data.append({"s": name, "t": e.title, "l": e.link, "img": img_url})
        except: continue
    return data

# --- UI ---
st.title("⚽ INFINITE SOURCE NEWSROOM")

if 'visual_feed' not in st.session_state:
    st.session_state.visual_feed = get_new_batch()

# 4-Column Responsive Grid
cols = st.columns(4)
for idx, item in enumerate(st.session_state.visual_feed):
    with cols[idx % 4]:
        st.markdown(f'''
            <div style="background-color:#111; padding:10px; border-radius:10px; border:1px solid #333; height:360px;">
                <img src="{item['img']}" style="width:100%; height:150px; object-fit:cover; border-radius:5px;">
                <p style="color:#00ff41; font-weight:bold; font-size:12px; margin:8px 0 0 0;">{item['s']}</p>
                <p style="font-size:14px; height:60px; overflow:hidden; font-weight:bold;">{item['t']}</p>
            </div>
        ''', unsafe_allow_html=True)
        if st.button("Generate Post", key=f"btn_{idx}"):
            st.session_state.active = item

# POST GENERATION
if 'active' in st.session_state:
    it = st.session_state.active
    st.divider()
    tag_line = f"#{it['s'].replace(' ', '')} #Soccer #Update2026 #Football"
    
    # FIXED SYNTAX HERE
    deep_text = f"📰 **THE DEEP SCOOP: {it['t'].upper()}**\n\n⚽ **BREAKING:** {it['t']}\n\n🔗 **FULL STORY:** {it['l']}\n\n{tag_line}"
    fast_text = f"⚡ **FAST UPDATE**\n\n📍 {it['t']}\n\n👉 Details: {it['l']}\n\n{tag_line}"

    c1, c2 = st.columns(2)
    with c1: 
        st.subheader("Deep Scoop")
        st.code(deep_text, language="markdown")
    with c2: 
        st.subheader("Fast Update")
        st.code(fast_text, language="markdown")

# REFRESH BUTTON
if st.button("🔄 REFRESH: SHOW 20 NEW SOURCES"):
    with st.spinner("Finding 20 different outlets..."):
        st.session_state.visual_feed = get_new_batch()
        st.rerun()
