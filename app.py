import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random
import base64

# --- CONFIG ---
st.set_page_config(page_title="Global Soccer Scout 2026", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #050505; }
    .stButton>button { background-color: #00ff41; color: black; font-weight: bold; }
    .news-card { background-color: #121212; padding: 15px; border-radius: 8px; border: 1px solid #333; margin-bottom: 10px; }
    .source-tag { color: #00ff41; font-size: 0.8rem; font-weight: bold; }
    .summary-text { color: #ccc; font-size: 0.9rem; line-height: 1.4; margin: 10px 0; font-family: sans-serif; }
    </style>
    """, unsafe_allow_html=True)

# --- 20+ GLOBAL SOURCES ---
MASTER_SOURCES = [
    ("Soccer Laduma", "https://www.snl24.com/soccerladuma/rss"),
    ("BBC Football", "https://push.api.bbci.co.uk/morph/items?page=1&limit=10&feed=football"),
    ("Sky Sports", "https://www.skysports.com/rss/12040"),
    ("Goal.com", "https://www.goal.com/en/feeds/news"),
    ("Transfermarkt", "https://www.transfermarkt.com/rss/news"),
    ("The Guardian", "https://www.theguardian.com/football/rss"),
    ("ESPN FC", "https://www.espn.com/espn/rss/soccer/news"),
    ("Marca", "https://e00-marca.uecdn.es/rss/en/index.xml"),
    ("AS English", "https://en.as.com/rss/en/football/index.xml"),
    ("Football Italia", "https://football-italia.net/feed/"),
    ("90min", "https://www.90min.com/posts.rss"),
    ("CaughtOffside", "https://www.caughtoffside.com/feed/"),
    ("OneFootball", "https://onefootball.com/en/rss"),
    ("World Soccer Talk", "https://worldsoccertalk.com/feed/"),
    ("KickOff", "https://www.snl24.com/kickoff/rss"),
    ("Daily Sun Sport", "https://www.snl24.com/dailysun/sport/rss"),
    ("Sowetan Live", "https://www.sowetanlive.co.za/sport/soccer/rss"),
    ("Google: Transfers", "https://news.google.com/rss/search?q=soccer+transfers+when:1h&hl=en-US&gl=US&ceid=US:en"),
    ("Google: Premier League", "https://news.google.com/rss/search?q=premier+league+news+when:1h&hl=en-US&gl=US&ceid=US:en"),
    ("Google: PSL News", "https://news.google.com/rss/search?q=PSL+soccer+South+Africa+when:1h&hl=en-ZA&gl=ZA&ceid=ZA:en"),
    ("Google: Champions League", "https://news.google.com/rss/search?q=champions+league+when:1h&hl=en-US&gl=US&ceid=US:en"),
    ("Daily Mail", "https://www.dailymail.co.uk/sport/football/index.rss")
]

def get_article_details(url):
    """Scrapes images and text. Handles Google News redirects."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        # Check if it's a Google News redirect and follow it
        r = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Image
        img_tag = soup.find("meta", property="og:image")
        img_url = img_tag["content"] if img_tag else None
        
        # Summary
        paras = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 70]
        summary = " ".join(paras[:3])
        
        return {"img": img_url, "summary": summary if summary else "Content is protected or hidden behind a paywall."}
    except:
        return None

def fetch_random_20():
    """Shuffles and picks 20 fresh items across sources."""
    shuffled_sources = list(MASTER_SOURCES)
    random.shuffle(shuffled_sources)
    final_list = []
    
    for name, url in shuffled_sources:
        if len(final_list) >= 20: break
        try:
            f = feedparser.parse(url)
            if f.entries:
                # Take 1-2 newest per source to ensure 20 distinct sources/stories
                for entry in f.entries[:2]:
                    if len(final_list) >= 20: break
                    final_list.append({'s': name, 't': entry.title, 'l': entry.link})
        except: continue
    return final_list

# --- UI ---
st.title("⚽ GLOBAL SOCCER SCOUT: 2026")

if st.button("🔄 SHUFFLE & FETCH 20 NEW SOURCES"):
    st.session_state.news_items = fetch_random_20()

if 'news_items' not in st.session_state:
    st.session_state.news_items = fetch_random_20()

for idx, item in enumerate(st.session_state.news_items, 1):
    with st.container():
        st.markdown(f'<div class="news-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="source-tag">{idx}. {item["s"].upper()}</div>', unsafe_allow_html=True)
        st.markdown(f'<a href="{item["l"]}" target="_blank" style="color:white; font-weight:bold; text-decoration:none; font-size:1.1rem;">{item["t"]}</a>', unsafe_allow_html=True)
        
        if st.button(f"🧠 Summarize & Grab Image #{idx}", key=f"btn_{idx}"):
            with st.spinner("Decoding link and analyzing..."):
                details = get_article_details(item['l'])
                if details:
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        if details['img']:
                            st.image(details['img'], use_container_width=True)
                            img_data = requests.get(details['img']).content
                            st.download_button("💾 Download", img_data, f"soccer_{idx}.jpg", "image/jpeg")
                    with c2:
                        st.markdown(f'<div class="summary-text">{details["summary"]}</div>', unsafe_allow_html=True)
                else:
                    st.error("This specific story is blocked from AI summary. Click the headline to read.")
        st.markdown('</div>', unsafe_allow_html=True)
