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
    .sentiment-tag { float: right; font-size: 0.75rem; padding: 2px 8px; border-radius: 5px; }
    .headline-link { color: #f0f6fc; font-weight: 600; text-decoration: none; font-size: 1.3rem; }
    .headline-link:hover { color: #238636; }
    </style>
    """, unsafe_allow_html=True)

# --- SOURCE POOL ---
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
    ("Daily Mail", "https://www.dailymail.co.uk/sport/football/index.rss"),
    ("Sowetan Live", "https://www.sowetanlive.co.za/sport/soccer/rss"),
    ("Football Italia", "https://football-italia.net/feed/"),
    ("TEAMtalk", "https://www.teamtalk.com/feed"),
    ("Ghana Soccernet", "https://ghanasoccernet.com/feed")
]

# --- UTILITY FUNCTIONS ---
def get_sentiment(text):
    """Simple keyword-based sentiment analysis."""
    hot_words = ['deal', 'official', 'winner', 'huge', 'breaking', 'signed', 'victory']
    sad_words = ['injury', 'lost', 'out', 'defeat', 'crisis', 'sacked', 'dropped']
    text = text.lower()
    if any(w in text for w in hot_words): return "🔥 HOT"
    if any(w in text for w in sad_words): return "⚠️ CRITICAL"
    return "ℹ️ NEUTRAL"

def get_scout_report(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=6)
        soup = BeautifulSoup(r.content, 'html.parser')
        img = soup.find("meta", property="og:image")
        paras = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 90]
        summary = " ".join(paras[:2]) if paras else "Full story available at the source link."
        return {"img": img["content"] if img else None, "text": summary}
    except:
        return None

def fetch_stories():
    random_sources = random.sample(MASTER_POOL, min(len(MASTER_POOL), 20))
    results = []
    for name, url in random_sources:
        try:
            f = feedparser.parse(url)
            if f.entries:
                entry = f.entries[0]
                results.append({
                    's': name, 
                    't': entry.title, 
                    'l': entry.link,
                    'sent': get_sentiment(entry.title)
                })
        except: continue
    return results

# --- SIDEBAR FILTERS ---
st.sidebar.title("🔍 Scout Filters")
search_query = st.sidebar.text_input("Search Players or Teams", "")
source_filter = st.sidebar.multiselect("Filter by Source", [s[0] for s in MASTER_POOL])

# --- APP LAYOUT ---
tab1, tab2 = st.tabs(["📢 Smart News Feed", "💬 AI Scout Chat"])

with tab1:
    st.title("⚽ GLOBAL SOCCER AGGREGATOR PRO")
    
    if st.button("🔄 REFRESH SCOUT REPORT"):
        st.session_state.news_feed = fetch_stories()

    if 'news_feed' not in st.session_state:
        st.session_state.news_feed = fetch_stories()

    # Filter Logic
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
        
        # Action Buttons
        col_btn, col_empty = st.columns([1, 3])
        if col_btn.button(f"✨ Prep FB Post #{i}", key=f"btn_{i}"):
            with st.spinner("Analyzing news context..."):
                data = get_scout_report(item['l'])
                if data:
                    fb_tags = f"#Soccer #Football #TransferNews #{item['s'].replace(' ', '')}"
                    fb_text = f"🚨 {item['sent']} UPDATE: {item['t'].upper()} 🚨\n\n⚽ THE SCOOP: {data['text']}\n\n🔗 Full story: {item['l']}\n\n{fb_tags}"
                    
                    st.info("Post Ready! Copy the text below:")
                    st.code(fb_text, language="markdown") # Better for copying
                    
                    if data['img']:
                        st.image(data['img'], width=400)
                else:
                    st.error("Could not fetch a deep summary for this link.")

with tab2:
    st.header("🤖 AI Scout Assistant")
    # (Same chat logic as your
