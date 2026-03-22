import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Elite 50 Soccer Scout", page_icon="⚽", layout="wide")

# --- 2. THE EXPANDED 50 SOURCE POOL ---
SOURCES = [
    # Global Giants
    ("Goal.com", "https://www.goal.com/en/feeds/news"), ("Sky Sports", "https://www.skysports.com/rss/12040"),
    ("BBC Sport", "http://newsrss.bbc.co.uk/rss/sportonline_uk_edition/football/rss.xml"), ("Transfermarkt", "https://www.transfermarkt.com/rss/news"),
    ("ESPN FC", "https://www.espn.com/espn/rss/soccer/news"), ("The Guardian", "https://www.theguardian.com/football/rss"),
    ("90min", "https://www.90min.com/posts.rss"), ("Marca", "https://e00-marca.uecdn.es/rss/en/index.xml"),
    ("AS English", "https://en.as.com/rss/en/football/index.xml"), ("Football Italia", "https://football-italia.net/feed/"),
    # Africa & Regional
    ("Soccer Laduma", "https://www.snl24.com/soccerladuma/rss"), ("KickOff", "https://www.snl24.com/kickoff/rss"),
    ("Ghana Soccernet", "https://ghanasoccernet.com/feed"), ("Sowetan Live", "https://www.sowetanlive.co.za/sport/soccer/rss"),
    ("iDiski Times", "https://www.idiskitimes.co.za/feed/"), ("FarPost", "https://farpost.co.za/feed/"),
    ("Soccernet NG", "https://soccernet.ng/feed/"), ("Brila FM", "https://www.brila.net/feed/"),
    ("CAF Online", "https://www.cafonline.com/rss"), ("The South African", "https://www.thesouthafrican.com/sport/soccer/feed/"),
    # Specialized & Tactical
    ("World Soccer", "https://www.worldsoccer.com/feed"), ("FourFourTwo", "https://www.fourfourtwo.com/rss.xml"),
    ("The Athletic", "https://theathletic.com/rss"), ("CaughtOffside", "https://www.caughtoffside.com/feed/"),
    ("TEAMtalk", "https://www.teamtalk.com/feed"), ("OneFootball", "https://onefootball.com/en/rss"),
    ("Squawka", "https://www.squawka.com/en/news/feed/"), ("World Football Index", "https://worldfootballindex.com/feed/"),
    # Club Specific / Fan Networks
    ("Barca Universal", "https://barcauniversal.com/feed/"), ("This Is Anfield", "https://www.thisisanfield.com/feed/"),
    ("Arseblog", "https://arseblog.news/feed/"), ("ToffeeWeb", "https://www.toffeeweb.com/rss/news.xml"),
    ("Juve FC", "https://www.juvefc.com/feed/"), ("Sempre Milan", "https://sempremilan.com/feed"),
    ("BVB Buzz", "https://bvbbuzz.com/feed/"), ("The Mag", "https://www.themag.co.uk/feed/"),
    # General & International
    ("Independent", "https://www.independent.co.uk/sport/football/rss"), ("Daily Mail", "https://www.dailymail.co.uk/sport/football/index.rss"),
    ("EuroSport", "https://www.eurosport.com/football/rss.xml"), ("Standard", "https://www.standard.co.uk/sport/football/rss"),
    ("Mirror Football", "https://www.mirror.co.uk/sport/football/rss.xml"), ("Daily Star", "https://www.dailystar.co.uk/sport/football/rss"),
    ("Express", "https://www.express.co.uk/posts/rss/65/football"), ("Tribal Football", "https://www.tribalfootball.com/rss.xml"),
    ("Football365", "https://www.football365.com/feed"), ("TalkSport", "https://talksport.com/football/feed/"),
    ("Daily Record", "https://www.dailyrecord.co.uk/sport/football/rss.xml"), ("Irish Times", "https://www.irishtimes.com/cmlink/news-soccer-1.1319114"),
    ("Sporting News", "https://www.sportingnews.com/us/rss/soccer"), ("SBNation", "https://www.sbnation.com/rss/current.xml")
]

# --- 3. QUEUE SYSTEM (ZERO-REPEAT) ---
if 'source_queue' not in st.session_state:
    all_s = SOURCES.copy()
    random.shuffle(all_s)
    st.session_state.source_queue = all_s
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
                r = requests.get(e.link, headers=headers, timeout=1.2)
                soup = BeautifulSoup(r.content, 'html.parser')
                img = soup.find("meta", property="og:image")
                img_url = img["content"] if img else "https://via.placeholder.com/400x225?text=Soccer+Scout"
                data.append({"s": name, "t": e.title, "l": e.link, "img": img_url})
        except: continue
    return data

def get_detailed_context(url):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=3)
        soup = BeautifulSoup(r.content, 'html.parser')
        paras = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 90]
        return paras[0] if paras else "Full details are available at the official source."
    except: return "Details are currently being updated by the newsroom."

# --- 4. UI INTERFACE ---
st.title("⚽ GLOBAL SOCCER HUB: 50 SOURCE NETWORK")
st.caption(f"Currently cycling through unique sources. Progress: {st.session_state.queue_index}/{len(SOURCES)}")

if 'visual_feed' not in st.session_state:
    st.session_state.visual_feed = fetch_next_20()

m_col, s_col = st.columns([4, 1.2])

with m_col:
    grid = st.columns(4)
    for idx, item in enumerate(st.session_state.visual_feed):
        with grid[idx % 4]:
            st.markdown(f'''
                <div style="background:#111; border-radius:12px; border:1px solid #333; margin-bottom:12px; height:370px; overflow:hidden;">
                    <img src="{item['img']}" style="width:100%; height:160px; object-fit:cover;">
                    <div style="padding:10px;">
                        <p style="color:#00ff41; font-size:10px; font-weight:bold; margin:0;">{item['s'].upper()}</p>
                        <p style="font-size:12px; font-weight:bold; color:white; margin-top:5px; height:50px; overflow:hidden;">{item['t']}</p>
                        <a href="{item['l']}" target="_blank" style="color:#888; font-size:10px; text-decoration:none;">🔗 Official Article</a>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            if st.button("🎤 DEEP SCOOP", key=f"btn_{idx}", use_container_width=True):
                st.session_state.active = item

with s_col:
    st.markdown("### 🔥 Trending #Tags")
    for t in ["#Amakhosi", "#RespectTheWork", "#Transfers2026", "#HereWeGo"]:
        st.markdown(f'<div style="background:#111; padding:10px; border-radius:8px; margin-bottom:8px; border-left:3px solid #00ff41; color:white; font-size:13px;">{t}</div>', unsafe_allow_html=True)
    if st.button("🔄 REFRESH: SHOW NEW", use_container_width=True):
        st.session_state.visual_feed = fetch_next_20()
        st.rerun()

# --- 5. THE "RESPECT THE WORK" GENERATOR ---
if 'active' in st.session_state:
    it = st.session_state.active
    st.divider()
    with st.spinner("Analyzing tactical radiography..."):
        full_context = get_detailed_context(it['l'])
        
        # YOUR CUSTOM "RESPECT" TEMPLATE
        scoop_response = (
            f"We always find something to say about **{it['s']}**... but let’s be honest for a second 🗣️\n\n"
            f"Every time they hit the headlines with news like **\"{it['t']}\"**, the quality and consistency keep coming! 📈\n\n"
            f"Maybe it’s time we give credit where it’s due. **The context:** {full_context[:300]}...\n\n"
            f"Solid, reliable, and always stepping up when it matters! Respect the silent work! 🛡️💎\n\n"
            f"👇 **FULL BREAKDOWN HERE:**\n"
            f"{it['l']}\n\n"
            f"#{it['s'].replace(' ', '')} #RespectTheWork #FootballUpdate #GameChanger #Soccer"
        )
        
        st.subheader(f"Insider Deep Scoop: {it['s']}")
        st.code(scoop_response, language="markdown")
