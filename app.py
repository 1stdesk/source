import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import re

# --- CONFIG ---
st.set_page_config(page_title="Pro Scout 20: Elite Edition", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .source-label { 
        background-color: #2e7bcf; color: white; padding: 2px 8px; 
        border-radius: 5px; font-size: 0.8rem; font-weight: bold;
    }
    .card {
        border: 1px solid #30363d; padding: 15px; border-radius: 10px;
        background-color: #161b22; margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- EXPANDED 20 SOURCES ---
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

def get_rich_content(url):
    """Deep scrapes for high-volume content."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=8)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Meta Data
        img = soup.find("meta", property="og:image")
        
        # Content Extraction - grabs all significant paragraphs
        paras = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 80]
        
        # Clean up text
        main_body = " ".join(paras[:6]) # Increased to 6 paragraphs for "more content"
        bullets = paras[:5] # Grab first 5 for the FB post
        
        return {
            "img": img["content"] if img else None,
            "body": main_body,
            "bullets": bullets
        }
    except:
        return None

# --- APP UI ---
st.title("⚽ PRO SCOUT 20: GLOBAL HUB")
st.write(f"Scanning **{len(MASTER_POOL)}** newsrooms for breaking updates...")

if 'feed_cache' not in st.session_state:
    with st.spinner("Initializing Global Feeds..."):
        results = []
        for name, url in MASTER_POOL:
            try:
                f = feedparser.parse(url)
                if f.entries:
                    results.append({"s": name, "t": f.entries[0].title, "l": f.entries[0].link})
            except: continue
        st.session_state.feed_cache = results

# Search bar to find specific players/teams in the 20 sources
search = st.text_input("🔍 Search within these 20 sources...", "")

# Display Logic
for i, item in enumerate(st.session_state.feed_cache):
    if search.lower() in item['t'].lower() or search.lower() in item['s'].lower():
        with st.container():
            st.markdown(f'<div class="card">', unsafe_allow_html=True)
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f'<span class="source-label">{item["s"]}</span>', unsafe_allow_html=True)
                st.subheader(item['t'])
            
            with col2:
                if st.button("🔥 Generate Post", key=f"btn_{i}"):
                    with st.spinner("Deep Scanning..."):
                        data = get_rich_content(item['l'])
                        if data:
                            # Constructing the massive FB post
                            bullet_str = "\n".join([f"📍 {b[:150]}..." for b in data['bullets']])
                            fb_template = (
                                f"🚨 BREAKING NEWS: {item['t'].upper()} 🚨\n\n"
                                f"Huge developments coming out of {item['s']} today. "
                                f"Here’s everything you need to know about this story:\n\n"
                                f"{bullet_str}\n\n"
                                f"🏟️ THE FULL SCOOP:\n{data['body'][:500]}...\n\n"
                                f"👇 READ MORE HERE:\n{item['l']}\n\n"
                                f"#Soccer #Football #TransferNews #{item['s'].replace(' ', '')} #MatchDay"
                            )
                            st.session_state[f"post_{i}"] = fb_template
                            st.session_state[f"img_{i}"] = data['img']
            
            # Show results if generated
            if f"post_{i}" in st.session_state:
                res_c1, res_c2 = st.columns([1, 2])
                with res_c1:
                    if st.session_state[f"img_{i}"]:
                        st.image(st.session_state[f"img_{i}"])
                with res_c2:
                    st.code(st.session_state[f"post_{i}"], language="markdown")
            
            st.markdown('</div>', unsafe_allow_html=True)

if st.button("♻️ Refresh All 20 Sources"):
    del st.session_state.feed_cache
    st.rerun()
