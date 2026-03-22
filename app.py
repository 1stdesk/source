import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random

# --- CONFIG ---
st.set_page_config(page_title="20-Source FB Scout", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #050505; }
    .stButton>button { background-color: #00ff41; color: black; font-weight: bold; border-radius: 20px; }
    .news-card { 
        background-color: #121212; 
        padding: 20px; 
        border-radius: 15px; 
        border: 1px solid #333; 
        margin-bottom: 20px;
    }
    .source-tag { color: #00ff41; font-weight: bold; font-size: 0.8rem; text-transform: uppercase; }
    .headline-link { color: white; font-weight: bold; text-decoration: none; font-size: 1.2rem; }
    </style>
    """, unsafe_allow_html=True)

# --- THE 20-SOURCE GENERATOR (From your list) ---
MASTER_POOL = [
    ("Goal.com", "https://www.goal.com/en/feeds/news"),
    ("Sky Sports", "https://www.skysports.com/rss/12040"),
    ("BBC Sport", "https://push.api.bbci.co.uk/morph/items?page=1&limit=10&feed=football"),
    ("Soccer Laduma", "https://www.snl24.com/soccerladuma/rss"),
    ("KickOff", "https://www.snl24.com/kickoff/rss"),
    ("ESPN FC", "https://www.espn.com/espn/rss/soccer/news"),
    ("Transfermarkt", "https://www.transfermarkt.com/rss/news"),
    ("The Guardian", "https://www.theguardian.com/football/rss"),
    ("90min", "https://www.90min.com/posts.rss"),
    ("CaughtOffside", "https://www.caughtoffside.com/feed/"),
    ("Marca", "https://e00-marca.uecdn.es/rss/en/index.xml"),
    ("AS English", "https://en.as.com/rss/en/football/index.xml"),
    ("FourFourTwo", "https://www.fourfourtwo.com/feeds/all"),
    ("TEAMtalk", "https://www.teamtalk.com/feed"),
    ("Football365", "https://www.football365.com/feed"),
    ("Ghana Soccernet", "https://ghanasoccernet.com/feed"),
    ("KingFut", "https://www.kingfut.com/feed/"),
    ("OneFootball", "https://onefootball.com/en/rss"),
    ("BeSoccer", "https://www.besoccer.com/rss"),
    ("101 Great Goals", "https://www.101greatgoals.com/feed/"),
    ("Football Italia", "https://football-italia.net/feed/"),
    ("Mundo Deportivo", "https://www.mundodeportivo.com/rss/futbol"),
    ("Sowetan Live", "https://www.sowetanlive.co.za/sport/soccer/rss"),
    ("Daily Sun", "https://www.snl24.com/dailysun/sport/rss"),
    ("The Athletic", "https://theathletic.com/football/?rss=1")
]

def get_fb_ready_scout(url):
    """Scrapes image and 2-sentence summary."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=6)
        soup = BeautifulSoup(r.content, 'html.parser')
        img = soup.find("meta", property="og:image")
        paras = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 90]
        return {"img": img["content"] if img else None, "text": " ".join(paras[:2])}
    except:
        return None

def fetch_20_unique():
    """Picks 20 random sources and gets 1 story from each."""
    random_sources = random.sample(MASTER_POOL, 20)
    results = []
    for name, url in random_sources:
        try:
            f = feedparser.parse(url)
            if f.entries:
                results.append({'s': name, 't': f.entries[0].title, 'l': f.entries[0].link})
        except: continue
    return results

# --- UI ---
st.title("⚽ 20-SOURCE GLOBAL SCOUT")
st.write("Every refresh picks 20 different sources from your master list.")

if st.button("🔄 REFRESH: GET 20 NEW SOURCES"):
    st.session_state.twenty_feed = fetch_20_unique()

if 'twenty_feed' not in st.session_state:
    st.session_state.twenty_feed = fetch_20_unique()

for i, item in enumerate(st.session_state.twenty_feed, 1):
    st.markdown(f'<div class="news-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="source-tag">{i}. {item["s"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<a href="{item["l"]}" target="_blank" class="headline-link">{item["t"]}</a>', unsafe_allow_html=True)
    
    if st.button(f"📝 Create Facebook Post #{i}", key=f"btn_{i}"):
        with st.spinner("Analyzing story..."):
            data = get_fb_ready_scout(item['l'])
            if data:
                # FB Post Formatting
                fb_text = f"🚨 SOCCER UPDATE: {item['t'].upper()} 🚨\n\n"
                fb_text += f"⚽ THE SCOOP: {data['text']}\n\n"
                fb_text += f"#Soccer #FootballNews #{item['s'].replace(' ', '')} #SportsUpdate"
                
                c1, c2 = st.columns([1, 2])
                with c1:
                    if data['img']:
                        st.image(data['img'])
                        st.download_button("💾 Save Image", requests.get(data['img']).content, f"fb_{i}.jpg")
                with c2:
                    st.text_area("COPY & PASTE TO FACEBOOK:", fb_text, height=200)
            else:
                st.error("Could not summarize this specific source.")
    st.markdown('</div>', unsafe_allow_html=True)
