import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random

# --- CONFIG ---
st.set_page_config(page_title="Infinite Soccer Scout", page_icon="⚽", layout="wide")

# --- MASSIVE SOURCE POOL ---
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
    ("Standard", "https://www.standard.co.uk/sport/football/rss"), ("Daily Star", "https://www.dailystar.co.uk/sport/football/rss"),
    ("Soccernet NG", "https://soccernet.ng/feed/"), ("Brila FM", "https://www.brila.net/feed/"),
    ("CAF Online", "https://www.cafonline.com/rss"), ("Barca Universal", "https://barcauniversal.com/feed/"),
    ("Juve FC", "https://www.juvefc.com/feed/"), ("Roma Press", "https://romapress.net/feed/"),
    ("The Mag", "https://www.themag.co.uk/feed/"), ("Arseblog", "https://arseblog.news/feed/"),
    ("This Is Anfield", "https://www.thisisanfield.com/feed/"), ("ToffeeWeb", "https://www.toffeeweb.com/rss/news.xml"),
    ("Daily Record", "https://www.dailyrecord.co.uk/sport/football/rss.xml")
]

def get_new_batch():
    current_names = [item['s'] for item in st.session_state.get('visual_feed', [])]
    available_pool = [s for s in BIG_POOL if s[0] not in current_names]
    
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
                img_url = img["content"] if img else "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?q=80&w=400&auto=format&fit=crop"
                data.append({"s": name, "t": e.title, "l": e.link, "img": img_url})
        except: continue
    return data

# --- UI ---
st.title("⚽ INFINITE SOURCE NEWSROOM")

if 'visual_feed' not in st.session_state:
    st.session_state.visual_feed = get_new_batch()

# 4-Column Grid with Full-Width Image Cards
cols = st.columns(4)
for idx, item in enumerate(st.session_state.visual_feed):
    with cols[idx % 4]:
        # Changed img style to object-fit: cover and width: 100%
        st.markdown(f'''
            <div style="background-color: rgb(17, 17, 17); padding: 0px; border-radius: 10px; border: 1px solid rgb(51, 51, 51); height: 400px; overflow: hidden; margin-bottom: 20px;">
                <img src="{item['img']}" style="width: 100%; height: 200px; object-fit: cover; border-bottom: 1px solid rgb(51, 51, 51);">
                <div style="padding: 10px;">
                    <p style="color: rgb(0, 255, 65); font-weight: bold; font-size: 11px; margin: 0px;">{item['s'].upper()}</p>
                    <p style="font-size: 14px; color: white; font-weight: bold; margin-top: 5px; height: 60px; overflow: hidden;">{item['t']}</p>
                </div>
            </div>
        ''', unsafe_allow_html=True)
        if st.button("Generate Post", key=f"btn_{idx}", use_container_width=True):
            st.session_state.active = item

# POST GENERATION
if 'active' in st.session_state:
    it = st.session_state.active
    st.divider()
    tag_line = f"#{it['s'].replace(' ', '')} #Soccer #Update2026 #Football"
    
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
if st.button("🔄 REFRESH: SHOW 20 NEW SOURCES", use_container_width=True):
    with st.spinner("Finding 20 different outlets..."):
        st.session_state.visual_feed = get_new_batch()
        st.rerun()
