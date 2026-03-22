import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random

# --- CONFIG ---
st.set_page_config(page_title="Elite Soccer Hub", page_icon="⚽", layout="wide")

# --- SOURCE POOL ---
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
    ("FourFourTwo", "https://www.fourfourtwo.com/rss.xml"), ("Daily Sun", "https://www.snl24.com/dailysun/sport/rss")
]

# --- SCRAPER LOGIC ---
def get_batch():
    selected = random.sample(BIG_POOL, 20)
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
st.title("⚽ GLOBAL SOCCER HUB: ENTERTAINMENT EDITION")

main_col, side_col = st.columns([3.5, 1])

with main_col:
    if 'visual_feed' not in st.session_state:
        st.session_state.visual_feed = get_batch()

    grid = st.columns(4)
    for idx, item in enumerate(st.session_state.visual_feed):
        with grid[idx % 4]:
            st.markdown(f'''
                <div style="background-color: #111; border-radius: 12px; border: 1px solid #333; margin-bottom: 15px; overflow: hidden; height: 380px;">
                    <img src="{item['img']}" style="width: 100%; height: 180px; object-fit: cover;">
                    <div style="padding: 12px;">
                        <p style="color: #00ff41; font-size: 10px; font-weight: bold; margin: 0;">{item['s'].upper()}</p>
                        <p style="font-size: 14px; font-weight: bold; color: white; margin-top: 5px; height: 50px; overflow: hidden;">{item['t']}</p>
                        <a href="{item['l']}" target="_blank" style="color: #00ff41; font-size: 12px; text-decoration: none;">🔥 Read Full Story</a>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            if st.button("🎤 Generate Viral Post", key=f"btn_{idx}", use_container_width=True):
                st.session_state.active = item

with side_col:
    st.markdown("### 🔥 Trending Social Pulse")
    trends = ["#TransferMadness", "Champions League Draw", "Mbappe Injury Update", "Ballon d'Or Race", "Next Chelsea Manager?"]
    for t in trends:
        st.markdown(f'<div style="background:#111; padding:10px; border-radius:8px; margin-bottom:8px; border-left:3px solid #00ff41;">{t}</div>', unsafe_allow_html=True)
    
    if st.button("🔄 Refresh Grid", use_container_width=True):
        st.session_state.visual_feed = get_batch()
        st.rerun()

# --- THE ENTERTAINING POST GENERATOR ---
if 'active' in st.session_state:
    it = st.session_state.active
    st.divider()
    
    # Logic for a "Hype" summary
    tags = f"#{it['s'].replace(' ', '')} #FootballNews #SoccerViral #GameOn #MatchDay"
    
    # 1. THE "VIRAL HOOK" POST
    viral_post = (
        f"🚨 **STOP WHAT YOU'RE DOING! THIS IS MASSIVE!** 🚨\n\n"
        f"The football world is absolutely buzzing right now because **{it['s']}** just dropped a bombshell:\n\n"
        f"🏆 **THE HEADLINE:** {it['t'].upper()}\n\n"
        f"You honestly cannot make this stuff up! Is this the turning point of the season? 🤔\n\n"
        f"👇 **GET THE FULL SCOOP HERE:**\n"
        f"{it['l']}\n\n"
        f"Drop a '🔥' if you saw this coming! {tags}"
    )

    # 2. THE "TV BROADCAST" POST
    tv_post = (
        f"🎤 **LIVE FROM THE NEWSROOM: THE DAILY SCOUT** 🎤\n\n"
        f"\"Good evening football fans, we're tracking a developing story from the {it['s']} camp...\"\n\n"
        f"📍 **THE SITUATION:** {it['t']}\n\n"
        f"Experts are already calling this one of the most talked-about moments of the week. "
        f"We are keeping a close eye on the fallout as it happens.\n\n"
        f"🔗 **OFFICIAL REPORT:** {it['l']}\n\n"
        f"Stay tuned for more. {tags}"
    )

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🔥 Viral 'Hype' Style")
        st.code(viral_post, language="markdown")
    with c2:
        st.subheader("📻 News 'Broadcast' Style")
        st.code(tv_post, language="markdown")
