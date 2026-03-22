import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Pro Soccer Scout AI", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #050505; color: white; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; background-color: #121212; border-radius: 10px; color: white; 
    }
    .stTabs [aria-selected="true"] { background-color: #00ff41; color: black; font-weight: bold; }
    .news-card { 
        background-color: #121212; padding: 20px; border-radius: 15px; 
        border: 1px solid #333; margin-bottom: 20px; 
    }
    .source-tag { color: #00ff41; font-weight: bold; font-size: 0.8rem; text-transform: uppercase; }
    .headline-link { color: white; font-weight: bold; text-decoration: none; font-size: 1.2rem; }
    .headline-link:hover { color: #00ff41; }
    </style>
    """, unsafe_allow_html=True)

# --- SOURCE POOL (From your list) ---
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
    ("OneFootball", "https://onefootball.com/en/rss"),
    ("BeSoccer", "https://www.besoccer.com/rss"),
    ("Daily Mail", "https://www.dailymail.co.uk/sport/football/index.rss"),
    ("Sowetan Live", "https://www.sowetanlive.co.za/sport/soccer/rss"),
    ("Daily Sun", "https://www.snl24.com/dailysun/sport/rss"),
    ("Football Italia", "https://football-italia.net/feed/"),
    ("TEAMtalk", "https://www.teamtalk.com/feed"),
    ("Ghana Soccernet", "https://ghanasoccernet.com/feed")
]

# --- UTILITY FUNCTIONS ---
def get_scout_report(url):
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
tab1, tab2 = st.tabs(["📢 Social News Feed", "💬 Chat with AI Scout"])

# TAB 1: NEWS FEED & FB GENERATOR
with tab1:
    st.title("⚽ GLOBAL SOCCER AGGREGATOR")
    
    if st.button("🔄 REFRESH: SCAN 20 NEW SOURCES"):
        st.session_state.news_feed = fetch_20()

    if 'news_feed' not in st.session_state:
        st.session_state.news_feed = fetch_20()

    for i, item in enumerate(st.session_state.news_feed, 1):
        st.markdown(f'<div class="news-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="source-tag">{i}. {item["s"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<a href="{item["l"]}" target="_blank" class="headline-link">{item["t"]}</a>', unsafe_allow_html=True)
        
        if st.button(f"✨ Generate Facebook Post #{i}", key=f"btn_{i}"):
            with st.spinner("Analyzing Story..."):
                data = get_scout_report(item['l'])
                if data:
                    fb_tags = f"#Soccer #Football #Update #{item['s'].replace(' ', '')} #Soccer2026"
                    fb_text = f"🚨 SOCCER UPDATE: {item['t'].upper()} 🚨\n\n⚽ THE SCOOP: {data['text']}\n\n👇 Full details at the link!\n\n{fb_tags}"
                    
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        if data['img']:
                            st.image(data['img'], caption="Story Image")
                            st.download_button("💾 Save Image", requests.get(data['img']).content, f"fb_post_{i}.jpg")
                    with c2:
                        st.text_area("📋 COPY & PASTE TO FACEBOOK:", fb_text, height=200, key=f"txt_{i}")
                else:
                    st.error("AI could not read this source. Try the next one!")
        st.markdown('</div>', unsafe_allow_html=True)

# TAB 2: INTERACTIVE AI CHAT
with tab2:
    st.header("🤖 AI Scout Assistant")
    st.caption("Ask me about specific teams, players, or transfers from the news above!")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "I've analyzed the 20 stories. Ask me about a team (e.g., 'United') or a player!"}]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("What is the latest on..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # LOGIC: SEARCH HEADLINES
        query = prompt.lower()
        matches = [n for n in st.session_state.news_feed if query in n['t'].lower() or query in n['s'].lower()]
        
        if matches:
            response = f"🎯 I found {len(matches)} match(es) in the current scout report:\n\n"
            for m in matches:
                response += f"- **{m['s']}** reports: *{m['t']}*\n"
            response += "\nWould you like me to summarize one of these for your Facebook page?"
        else:
            response = "🔍 I don't see that specific name in the current 20 stories. I do see a lot of updates from **" + st.session_state.news_feed[0]['s'] + "** and **" + st.session_state.news_feed[1]['s'] + "**. Try asking about them!"

        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
