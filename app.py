import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random

# --- CONFIG ---
st.set_page_config(page_title="Elite 50 Soccer Insider", page_icon="⚽", layout="wide")

# --- THE 50 SOURCE POOL ---
SOURCES = [
    # Global & European Giants
    ("Goal.com", "https://www.goal.com/en/feeds/news"), ("Sky Sports", "https://www.skysports.com/rss/12040"),
    ("BBC Sport", "http://newsrss.bbc.co.uk/rss/sportonline_uk_edition/football/rss.xml"), ("Transfermarkt", "https://www.transfermarkt.com/rss/news"),
    ("ESPN FC", "https://www.espn.com/espn/rss/soccer/news"), ("The Guardian", "https://www.theguardian.com/football/rss"),
    ("90min", "https://www.90min.com/posts.rss"), ("Marca", "https://e00-marca.uecdn.es/rss/en/index.xml"),
    ("AS English", "https://en.as.com/rss/en/football/index.xml"), ("Football Italia", "https://football-italia.net/feed/"),
    ("EuroSport", "https://www.eurosport.com/football/rss.xml"), ("The Athletic", "https://theathletic.com/rss"),
    # South African & African Experts
    ("Soccer Laduma", "https://www.snl24.com/soccerladuma/rss"), ("KickOff", "https://www.snl24.com/kickoff/rss"),
    ("iDiski Times", "https://www.idiskitimes.co.za/feed/"), ("FarPost", "https://farpost.co.za/feed/"),
    ("Sowetan Live", "https://www.sowetanlive.co.za/sport/soccer/rss"), ("Soccernet NG", "https://soccernet.ng/feed/"),
    ("Brila FM", "https://www.brila.net/feed/"), ("CAF Online", "https://www.cafonline.com/rss"),
    ("The South African", "https://www.thesouthafrican.com/sport/soccer/feed/"), ("Foot Africa", "https://foot-africa.com/en/feed/"),
    # Tactical & Specialist
    ("World Soccer Talk", "https://worldsoccertalk.com/feed/"), ("FourFourTwo", "https://www.fourfourtwo.com/rss.xml"),
    ("CaughtOffside", "https://www.caughtoffside.com/feed/"), ("TEAMtalk", "https://www.teamtalk.com/feed"),
    ("OneFootball", "https://onefootball.com/en/rss"), ("Squawka", "https://www.squawka.com/en/news/feed/"),
    ("Football365", "https://www.football365.com/feed"), ("World Football Index", "https://worldfootballindex.com/feed/"),
    # Club & Fan Specific
    ("Barca Universal", "https://barcauniversal.com/feed/"), ("This Is Anfield", "https://www.thisisanfield.com/feed/"),
    ("Arseblog", "https://arseblog.news/feed/"), ("ToffeeWeb", "https://www.toffeeweb.com/rss/news.xml"),
    ("Juve FC", "https://www.juvefc.com/feed/"), ("Sempre Milan", "https://sempremilan.com/feed"),
    ("The Mag", "https://www.themag.co.uk/feed/"), ("United In Focus", "https://www.unitedinfocus.com/feed/"),
    # General High-Volume News
    ("Independent", "https://www.independent.co.uk/sport/football/rss"), ("Daily Mail", "https://www.dailymail.co.uk/sport/football/index.rss"),
    ("Standard", "https://www.standard.co.uk/sport/football/rss"), ("Daily Record", "https://www.dailyrecord.co.uk/sport/football/rss.xml"),
    ("Irish Times Soccer", "https://www.irishtimes.com/cmlink/news-soccer-1.1319114"), ("Sporting News", "https://www.sportingnews.com/us/rss/soccer"),
    ("Daily Express", "https://www.express.co.uk/posts/rss/65/football"), ("Daily Star", "https://www.dailystar.co.uk/sport/football/rss"),
    ("Tribal Football", "https://www.tribalfootball.com/rss.xml"), ("The Sun", "https://www.thesun.co.uk/sport/football/feed/"),
    ("SBNation Soccer", "https://www.sbnation.com/rss/soccer/current.xml"), ("TalkSport", "https://talksport.com/football/feed/")
]

# --- SESSION & QUEUE LOGIC ---
if 'source_queue' not in st.session_state:
    all_s = SOURCES.copy()
    random.shuffle(all_s) # Randomize the initial order
    st.session_state.source_queue = all_s
    st.session_state.queue_index = 0

def fetch_next_batch():
    """Cycles to the next 20 sources in the 50-source list."""
    # Reset and reshuffle if we've reached the end
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
                # Scrape Thumbnail
                r = requests.get(e.link, headers=headers, timeout=1.2)
                soup = BeautifulSoup(r.content, 'html.parser')
                img = soup.find("meta", property="og:image")
                img_url = img["content"] if img else "https://via.placeholder.com/400x225?text=Soccer+News"
                data.append({"s": name, "t": e.title, "l": e.link, "img": img_url})
        except: continue
    return data

def get_deep_summary(url):
    """Scrapes context for the 'Respect the Work' post."""
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=3)
        soup = BeautifulSoup(r.content, 'html.parser')
        paras = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 100]
        return paras[0] if paras else "Full details are available at the link."
    except: return "Context is being verified by the scouts..."

# --- UI INTERFACE ---
st.title("⚽ 50-SOURCE SOCCER COMMAND CENTER")
st.caption(f"Zero-Repeat Mode: Showing batch starting at index {st.session_state.queue_index} of {len(SOURCES)} sources.")

if 'visual_feed' not in st.session_state:
    st.session_state.visual_feed = fetch_next_batch()

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
                        <a href="{item['l']}" target="_blank" style="color:#888; font-size:10px; text-decoration:none;">🔗 Original Article</a>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            if st.button("🎤 DEEP SCOOP", key=f"btn_{idx}", use_container_width=True):
                st.session_state.active = item

with s_col:
    st.markdown("### 🔥 Trending Social")
    for t in ["#Amakhosi", "#RespectTheWork", "#Transfers2026", "#HereWeGo"]:
        st.markdown(f'<div style="background:#111; padding:10px; border-radius:8px; margin-bottom:8px; border-left:3px solid #00ff41; color:white; font-size:13px;">{t}</div>', unsafe_allow_html=True)
    if st.button("🔄 REFRESH: 20 NEW SOURCES", use_container_width=True):
        st.session_state.visual_feed = fetch_next_batch()
        st.rerun()

# --- THE "RESPECT THE WORK" GENERATOR ---
if 'active' in st.session_state:
    it = st.session_state.active
    st.divider()
    with st.spinner("Decoding tactical radiography..."):
        full_context = get_deep_summary(it['l'])
        
        scoop_response = (
            f"We always find something to say about **{it['s']}**... but let’s be honest for a second 🗣️\n\n"
            f"Every time they hit the headlines with news like **\"{it['t']}\"**, the quality and consistency keep coming! 📈\n\n"
            f"Maybe it’s time we give credit where it’s due. **The scoop:** {full_context[:350]}...\n\n"
            f"Solid, reliable, and always stepping up when it matters! Respect the silent work! 🛡️💎\n\n"
            f"👇 **FULL BREAKDOWN HERE:**\n"
            f"{it['l']}\n\n"
            f"#{it['s'].replace(' ', '')} #RespectTheWork #FootballNews #GameChanger #Soccer"
        )
        
        st.subheader(f"Insider Deep Scoop: {it['s']}")
        st.code(scoop_response, language="markdown")
