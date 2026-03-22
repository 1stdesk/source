import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import re

# --- CONFIG ---
st.set_page_config(page_title="Pro Scout: Content Max", page_icon="⚽", layout="wide")

# --- STYLING (Dark Mode Professional) ---
st.markdown("""
    <style>
    .report-box { 
        background-color: #111; padding: 20px; border-radius: 10px; 
        border: 1px solid #00ff41; margin-bottom: 25px;
    }
    .stCode { background-color: #000 !important; }
    </style>
    """, unsafe_allow_html=True)

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
    ("Football Italia", "https://football-italia.net/feed/")
]

# --- NEW: DEEP CONTENT EXTRACTION ---
def get_deep_content(url):
    """Extracts a larger chunk of text and identifies key entities."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Get image
        img = soup.find("meta", property="og:image")
        img_url = img["content"] if img else None
        
        # Get all meaningful paragraphs
        paragraphs = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 100]
        
        # Create a "Mega Summary" (first 4-5 paragraphs)
        full_text = " ".join(paragraphs[:5])
        
        # Clean up text (remove extra whitespace)
        full_text = re.sub(r'\s+', ' ', full_text)
        
        return {"img": img_url, "content": full_text, "bullets": paragraphs[:4]}
    except Exception as e:
        return None

# --- APP INTERFACE ---
st.title("⚽ High-Content Soccer Aggregator")
st.subheader("Deep-scanned news for detailed Facebook updates")

if 'full_feed' not in st.session_state:
    with st.spinner("Syncing all major networks..."):
        feeds = []
        for name, url in MASTER_POOL:
            f = feedparser.parse(url)
            if f.entries:
                feeds.append({"s": name, "t": f.entries[0].title, "l": f.entries[0].link})
        st.session_state.full_feed = feeds

# Display all sources
for i, item in enumerate(st.session_state.full_feed):
    with st.expander(f"📰 {item['s']}: {item['t']}", expanded=False):
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.write(f"**Source:** {item['s']}")
            if st.button(f"🔍 Deep Scan & Generate", key=f"btn_{i}"):
                with st.spinner("Extracting detailed intel..."):
                    data = get_deep_content(item['l'])
                    if data:
                        # Build the Content-Heavy Facebook Post
                        bullet_points = "\n".join([f"🔹 {b[:120]}..." for b in data['bullets']])
                        
                        rich_fb_post = (
                            f"📢 **BIG READ: {item['t'].upper()}** 📢\n\n"
                            f"The latest from {item['s']} is making waves in the football world. "
                            f"Here is the detailed breakdown of what's happening right now:\n\n"
                            f"{bullet_points}\n\n"
                            f"🤔 What’s your take on this move? Drop a comment below! 👇\n\n"
                            f"Full Story here: {item['l']}\n\n"
                            f"#FootballNews #SoccerUpdate #TransferMarket #{item['s'].replace('.','')}"
                        )
                        
                        st.session_state[f"post_{i}"] = rich_fb_post
                        st.session_state[f"img_{i}"] = data['img']
        
        with col2:
            if f"post_{i}" in st.session_state:
                st.image(st.session_state[f"img_{i}"], use_container_width=True)
                st.markdown("**Professional Facebook Copy:**")
                st.code(st.session_state[f"post_{i}"], language="markdown")
            else:
                st.info("Click 'Deep Scan' to generate long-form content.")

# --- FOOTER ---
if st.button("♻️ Refresh All Sources"):
    del st.session_state.full_feed
    st.rerun()
