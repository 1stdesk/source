import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random

# --- CONFIG ---
st.set_page_config(page_title="Ultra Soccer AI Scout 2026", page_icon="⚽", layout="wide")

# Custom Styling (Dark/Matrix/Social Ready)
st.markdown("""
    <style>
    .main { background-color: #050505; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #121212; border-radius: 10px 10px 0 0; color: white; }
    .stTabs [aria-selected="true"] { background-color: #00ff41; color: black; font-weight: bold; }
    .news-card { background-color: #121212; padding: 20px; border-radius: 15px; border: 1px solid #333; margin-bottom: 20px; }
    .source-tag { color: #00ff41; font-weight: bold; font-size: 0.8rem; text-transform: uppercase; }
    .headline-link { color: white; font-weight: bold; text-decoration: none; font-size: 1.2rem; }
    </style>
    """, unsafe_allow_html=True)

# --- MASTER SOURCES (25+ from your list) ---
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
    ("Football365", "https://www.football365.com/feed"),
    ("Ghana Soccernet", "https://ghanasoccernet.com/feed"),
    ("KingFut", "https://www.kingfut.com/feed/"),
    ("OneFootball", "https://onefootball.com/en/rss"),
    ("BeSoccer", "https://www.besoccer.com/rss"),
    ("Football Italia", "https://football-italia.net/feed/"),
    ("Daily Mail", "https://www.dailymail.co.uk/sport/football/index.rss"),
    ("Sowetan Live", "https://www.sowetanlive.co.za/sport/soccer/rss"),
    ("Daily Sun", "https://www.snl24.com/dailysun/sport/rss"),
    ("The Athletic", "https://theathletic.com/football/?rss=1"),
    ("FourFourTwo", "https://www.fourfourtwo.com/feeds/all"),
    ("TEAMtalk", "https://www.teamtalk.com/feed")
]

# --- FUNCTIONS ---
def get_scout_data(url):
    """Scrapes images and text summaries."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=6)
        soup = BeautifulSoup(r.content, 'html.parser')
        img = soup.find("meta", property="og:image")
        paras = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 95]
        return {"img": img["content"] if img else None, "text": " ".join(paras[:2])}
    except:
        return None

def fetch_20():
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

# --- APP LAYOUT ---
tab1, tab2 = st.tabs(["📢 Global Scout Feed", "💬 Chat with Scout"])

with tab1:
    st.title("⚽ ULTRA SOCCER AGGREGATOR")
    if st.button("🔄 REFRESH: FETCH 20 NEW SOURCES"):
        st.session_state.news_feed = fetch_20()

    if 'news_feed' not in st.session_state:
        st.session_state.news_feed = fetch_20()

    for i, item in enumerate(st.session_state.news_feed, 1):
        st.markdown(f'<div class="news-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="source-tag">{i}. {item["s"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<a href="{item["l"]}" target="_blank" class="headline-link">{item["t"]}</a>', unsafe_allow_html=True)
        
        if st.button(f"✨ Generate FB Post #{i}", key=f"btn_{i}"):
            with st.spinner("Analyzing Story..."):
                data = get_scout_data(item['l'])
                if data:
                    # Facebook Post Format
                    tags = f"#Soccer #FootballNews #{item['s'].replace(' ', '')} #Soccer2026"
                    fb_text = f"🚨 SOCCER UPDATE: {item['t'].upper()} 🚨\n\n⚽ THE SCOOP: {data['text']}\n\n👉 Click link for full story!\n\n{tags}"
                    
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        if data['img']:
                            st.image(data['img'])
                            st.download_button("💾 Save Pic", requests.get(data['img']).content, f"scout_{i}.jpg")
                    with c2:
                        st.text_area("COPY FOR FACEBOOK:", fb_text, height=220, key=f"txt_{i}")
                else:
                    st.error("Could not scrape this source.")
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.header("🤖 AI Scout Assistant")
    st.caption("Ask me about the headlines we just pulled!")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about today's news..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Simple local AI logic
        context_headlines = [i['t'] for i in st.session_state.news_feed]
        if any(keyword in prompt.lower() for keyword in ["transfer", "sign", "buy", "sell"]):
            response = "Scanning transfers... I see headlines regarding " + ", ".join(context_headlines[:2]) + ". Want a full summary of one?"
        else:
            response = "I've analyzed the 20 fresh sources. Most stories today are coming from " + st.session_state.news_feed[0]['s'] + " and " + st.session_state.news_feed[1]['s'] + ". What would you like to know?"
            
        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
