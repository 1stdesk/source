import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Pro Soccer Scout AI v2", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; background-color: #161b22; border-radius: 10px; color: white; 
    }
    .stTabs [aria-selected="true"] { background-color: #238636; color: white; font-weight: bold; }
    .news-card { 
        background-color: #161b22; padding: 25px; border-radius: 12px; 
        border: 1px solid #30363d; margin-bottom: 25px;
        transition: transform 0.2s;
    }
    .news-card:hover { border-color: #238636; transform: translateY(-2px); }
    .source-tag { color: #58a6ff; font-weight: bold; font-size: 0.85rem; margin-bottom: 10px; }
    .sentiment-tag { float: right; font-size: 0.75rem; padding: 2px 8px; border-radius: 5px; background: #21262d;}
    .headline-link { color: #f0f6fc; font-weight: 600; text-decoration: none; font-size: 1.3rem; }
    .headline-link:hover { color: #238636; }
    </style>
    """, unsafe_allow_html=True)

# --- SOURCE POOL ---
MASTER_POOL = [
    ("Goal.com", "https://www.goal.com/en/feeds/news"),
    ("Sky Sports", "https://www.skysports.com/rss/12040"),
    ("BBC Sport", "https://push.api.bbci.co.uk/morph/items?page=1&limit=10&feed=football"),
    ("ESPN FC", "https://www.espn.com/espn/rss/soccer/news"),
    ("Transfermarkt", "https://www.transfermarkt.com/rss/news"),
    ("90min", "https://www.90min.com/posts.rss"),
    ("Daily Mail", "https://www.dailymail.co.uk/sport/football/index.rss")
]

# --- UTILITY FUNCTIONS ---
def get_sentiment(text):
    hot_words = ['deal', 'official', 'winner', 'huge', 'breaking', 'signed', 'victory', 'done']
    sad_words = ['injury', 'lost', 'out', 'defeat', 'crisis', 'sacked', 'dropped', 'misses']
    text = text.lower()
    if any(w in text for w in hot_words): return "🔥 HOT"
    if any(w in text for w in sad_words): return "⚠️ CRITICAL"
    return "ℹ️ NEUTRAL"

@st.cache_data(ttl=600)
def fetch_stories():
    results = []
    for name, url in MASTER_POOL:
        try:
            f = feedparser.parse(url)
            for entry in f.entries[:3]: # Get top 3 from each source
                results.append({
                    's': name, 
                    't': entry.title, 
                    'l': entry.link,
                    'sent': get_sentiment(entry.title)
                })
        except: continue
    random.shuffle(results)
    return results

def get_scout_report(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(url, headers=headers, timeout=6)
        soup = BeautifulSoup(r.content, 'html.parser')
        img = soup.find("meta", property="og:image")
        paras = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 90]
        summary = " ".join(paras[:2]) if paras else "Full story available at the source link."
        return {"img": img["content"] if img else None, "text": summary}
    except:
        return None

# --- SIDEBAR FILTERS ---
st.sidebar.title("🔍 Scout Filters")
search_query = st.sidebar.text_input("Search Players or Teams", "")
source_filter = st.sidebar.multiselect("Filter by Source", [s[0] for s in MASTER_POOL])

# --- APP LAYOUT ---
tab1, tab2 = st.tabs(["📢 Smart News Feed", "💬 AI Scout Chat"])

with tab1:
    st.title("⚽ GLOBAL SOCCER AGGREGATOR PRO")
    
    if st.button("🔄 REFRESH SCOUT REPORT"):
        st.cache_data.clear()
        st.session_state.news_feed = fetch_stories()

    if 'news_feed' not in st.session_state:
        st.session_state.news_feed = fetch_stories()

    display_feed = st.session_state.news_feed
    if search_query:
        display_feed = [n for n in display_feed if search_query.lower() in n['t'].lower()]
    if source_filter:
        display_feed = [n for n in display_feed if n['s'] in source_filter]

    for i, item in enumerate(display_feed, 1):
        st.markdown(f'''
            <div class="news-card">
                <span class="sentiment-tag">{item['sent']}</span>
                <div class="source-tag">{item["s"]}</div>
                <a href="{item["l"]}" target="_blank" class="headline-link">{item["t"]}</a>
            </div>
        ''', unsafe_allow_html=True)
        
        col_btn, col_empty = st.columns([1, 3])
        if col_btn.button(f"✨ Prep FB Post", key=f"btn_{i}"):
            with st.spinner("Analyzing context..."):
                data = get_scout_report(item['l'])
                if data:
                    fb_text = f"🚨 {item['sent']} UPDATE: {item['t'].upper()} 🚨\n\n⚽ THE SCOOP: {data['text'][:300]}...\n\n🔗 Full story: {item['l']}"
                    st.code(fb_text, language="markdown")
                    if data['img']: st.image(data['img'], width=400)
                else:
                    st.error("Could not fetch details.")

with tab2:
    st.header("🤖 AI Scout Assistant")
    st.write("Ask me about the latest headlines or player stats.")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Ready to scout. What's on your mind?"}]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask about a transfer..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            # Simple Logic: Check if the user is asking about something in the feed
            relevant_news = [n['t'] for n in display_feed if prompt.lower() in n['t'].lower()]
            
            if relevant_news:
                response = f"I found {len(relevant_news)} relevant updates for you: \n\n" + "\n- ".join(relevant_news)
            else:
                response = "I'm not seeing any breaking news on that specifically in the current feed, but I'll keep an eye on the wires for you."
            
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
