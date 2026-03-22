import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import time

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Pro Soccer Scout - ALL SOURCES", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #050505; color: #e0e0e0; }
    [data-testid="stMetricValue"] { font-size: 1.5rem; color: #00ff41; }
    .source-header { 
        background: linear-gradient(90deg, #1e1e1e, #000);
        padding: 10px; border-radius: 5px; border-left: 5px solid #00ff41;
        margin-bottom: 15px; font-weight: bold;
    }
    .news-item { border-bottom: 1px solid #333; padding: 10px 0; }
    .news-link { color: #00ff41; text-decoration: none; font-size: 1.1rem; }
    .news-link:hover { text-decoration: underline; color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

# --- COMPLETE SOURCE LIST ---
MASTER_POOL = [
    ("Goal.com", "https://www.goal.com/en/feeds/news"),
    ("Sky Sports", "https://www.skysports.com/rss/12040"),
    ("BBC Sport", "http://newsrss.bbc.co.uk/rss/sportonline_uk_edition/football/rss.xml"),
    ("Soccer Laduma", "https://www.snl24.com/soccerladuma/rss"),
    ("KickOff", "https://www.snl24.com/kickoff/rss"),
    ("ESPN FC", "https://www.espn.com/espn/rss/soccer/news"),
    ("Transfermarkt", "https://www.transfermarkt.com/rss/news"),
    ("The Guardian", "https://www.theguardian.com/football/rss"),
    ("90min", "https://www.90min.com/posts.rss"),
    ("CaughtOffside", "https://www.caughtoffside.com/feed/"),
    ("Marca", "https://e00-marca.uecdn.es/rss/en/index.xml"),
    ("AS English", "https://en.as.com/rss/en/football/index.xml"),
    ("Daily Mail", "https://www.dailymail.co.uk/sport/football/index.rss"),
    ("Sowetan Live", "https://www.sowetanlive.co.za/sport/soccer/rss"),
    ("Daily Sun", "https://www.snl24.com/dailysun/sport/rss"),
    ("Football Italia", "https://football-italia.net/feed/"),
    ("TEAMtalk", "https://www.teamtalk.com/feed"),
    ("Ghana Soccernet", "https://ghanasoccernet.com/feed"),
    ("World Soccer", "https://www.worldsoccer.com/feed"),
    ("FourFourTwo", "https://www.fourfourtwo.com/rss.xml")
]

# --- CORE FUNCTIONS ---
def fetch_all_sources():
    """Fetches the latest headline from EVERY source."""
    all_data = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, (name, url) in enumerate(MASTER_POOL):
        status_text.text(f"Scanning {name}...")
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                entry = feed.entries[0]
                all_data.append({
                    "source": name,
                    "title": entry.title,
                    "link": entry.link,
                    "date": entry.get('published', 'Recently')
                })
        except:
            continue
        progress_bar.progress((idx + 1) / len(MASTER_POOL))
    
    status_text.empty()
    progress_bar.empty()
    return all_data

# --- APP LAYOUT ---
st.title("⚽ The Full Scout Dashboard")
st.caption(f"Currently monitoring **{len(MASTER_POOL)}** global sources.")

# Sidebar Controls
with st.sidebar:
    st.header("Settings")
    view_mode = st.radio("Display Mode", ["List View", "Compact Grid"])
    if st.button("🚀 SYNC ALL SOURCES"):
        st.session_state.all_news = fetch_all_sources()

# Initialize session state
if 'all_news' not in st.session_state:
    st.session_state.all_news = fetch_all_sources()

# --- DISPLAY LOGIC ---
if view_mode == "List View":
    for item in st.session_state.all_news:
        st.markdown(f'<div class="source-header">{item["source"]}</div>', unsafe_allow_html=True)
        st.markdown(f'''
            <div class="news-item">
                <a class="news-link" href="{item['link']}" target="_blank">{item['title']}</a><br>
                <small style="color: #888;">{item['date']}</small>
            </div>
        ''', unsafe_allow_html=True)
        
        # Generator Button for this specific item
        if st.button(f"Generate Content for {item['source']}", key=item['source']):
            st.success(f"Context: {item['title']}. Ready to post to Social Media!")
        st.write("---")

else:
    # Compact Grid View
    cols = st.columns(3)
    for idx, item in enumerate(st.session_state.all_news):
        with cols[idx % 3]:
            with st.container(border=True):
                st.markdown(f"**{item['source']}**")
                st.write(item['title'])
                st.page_link(item['link'], label="Read Story", icon="🔗")

# --- FOOTER ---
st.markdown("---")
st.info("💡 **Pro Tip:** Use the 'Sync' button in the sidebar to get the absolute latest updates from all 20 servers.")
