import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random

# --- CONFIG ---
st.set_page_config(page_title="Soccer AI Scout 2026", page_icon="⚽", layout="wide")

# Matrix/Dark Theme
st.markdown("""
    <style>
    .main { background-color: #050505; }
    .news-card { 
        background-color: #121212; 
        padding: 15px; 
        border-radius: 10px; 
        border: 1px solid #333; 
        margin-bottom: 15px;
    }
    .source-tag { color: #00ff41; font-weight: bold; font-size: 0.8rem; }
    .summary-box { 
        color: #d1d1d1; 
        font-size: 0.9rem; 
        background-color: #1a1a1a; 
        padding: 10px; 
        border-radius: 5px;
        margin-top: 10px;
    }
    .headline-link { color: white; font-weight: bold; text-decoration: none; font-size: 1.1rem; }
    .headline-link:hover { color: #00ff41; }
    </style>
    """, unsafe_allow_html=True)

# 20+ Global Soccer Sources
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
    ("Google: PSL News", "https://news.google.com/rss/search?q=PSL+soccer+South+Africa+when:1h&hl=en-ZA&gl=ZA&ceid=ZA:en")
]

def get_ai_scout_data(url):
    """Follows redirects and grabs the story's main image and summary."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        # allow_redirects=True is CRITICAL for Google News links
        r = requests.get(url, headers=headers, timeout=7, allow_redirects=True)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # 1. Grab Main Story Image
        img_url = None
        img_meta = soup.find("meta", property="og:image")
        if img_meta:
            img_url = img_meta["content"]
        
        # 2. Grab Short Summary (First 2-3 significant paragraphs)
        paras = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 80]
        summary = " ".join(paras[:2]) # Short and sweet
        
        return {"img": img_url, "text": summary}
    except:
        return None

def refresh_pool():
    shuffled = list(MASTER_SOURCES)
    random.shuffle(shuffled)
    news = []
    for name, url in shuffled:
        if len(news) >= 20: break
        try:
            f = feedparser.parse(url)
            for entry in f.entries[:1]: # Take the absolute freshest story
                news.append({'s': name, 't': entry.title, 'l': entry.link})
        except: continue
    return news

# --- UI ---
st.title("⚽ GLOBAL SOCCER AI SCOUT")

if st.button("🔄 SHUFFLE 20 NEW STORIES"):
    st.session_state.news_feed = refresh_pool()

if 'news_feed' not in st.session_state:
    st.session_state.news_feed = refresh_pool()

for i, item in enumerate(st.session_state.news_feed, 1):
    st.markdown(f'<div class="news-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="source-tag">{i}. {item["s"].upper()}</div>', unsafe_allow_html=True)
    st.markdown(f'<a href="{item["l"]}" target="_blank" class="headline-link">{item["t"]}</a>', unsafe_allow_html=True)
    
    # Process Button
    if st.button(f"🧠 Summarize Story #{i}", key=f"btn_{i}"):
        with st.spinner("Analyzing source..."):
            data = get_ai_scout_data(item['l'])
            if data:
                col_img, col_txt = st.columns([1, 3])
                with col_img:
                    if data['img']:
                        st.image(data['img'], use_container_width=True)
                        # Quick download for the image
                        img_res = requests.get(data['img']).content
                        st.download_button("💾 Save Image", img_res, f"soccer_pic_{i}.jpg", "image/jpeg")
                with col_txt:
                    st.markdown(f'<div class="summary-box"><b>AI SUMMARY:</b><br>{data["text"]}</div>', unsafe_allow_html=True)
            else:
                st.error("Could not summarize. The site might be blocking AI access.")
    st.markdown('</div>', unsafe_allow_html=True)
