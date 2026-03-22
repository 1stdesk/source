import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random
import re

# --- CONFIG ---
st.set_page_config(page_title="Soccer Social Trends 2026", page_icon="🔥", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #161b22; border-radius: 10px; color: white; }
    .stTabs [aria-selected="true"] { background-color: #238636; color: white; font-weight: bold; }
    .news-card { 
        background-color: #161b22; padding: 18px; border-radius: 12px; 
        border: 1px solid #30363d; margin-bottom: 15px;
    }
    .source-tag { color: #58a6ff; font-weight: bold; font-size: 0.75rem; text-transform: uppercase; }
    .headline-link { color: #f0f6fc; font-weight: bold; text-decoration: none; font-size: 1.1rem; }
    .summary-box { 
        background-color: #0d1117; padding: 25px; border-radius: 10px; 
        border: 1px solid #238636; margin-top: 15px; line-height: 1.8; color: #e6edf3;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SOURCE POOL (Refined for Social Speed) ---
MASTER_POOL = [
    ("Goal Viral", "https://www.goal.com/en/feeds/news"),
    ("Sky Breaking", "https://www.skysports.com/rss/12040"),
    ("BBC Social", "https://push.api.bbci.co.uk/morph/items?page=1&limit=10&feed=football"),
    ("Soccer Laduma", "https://www.snl24.com/soccerladuma/rss"),
    ("KickOff Trending", "https://www.snl24.com/kickoff/rss"),
    ("Transfer News Live", "https://www.transfermarkt.com/rss/news"),
    ("90min Social", "https://www.90min.com/posts.rss"),
    ("CaughtOffside", "https://www.caughtoffside.com/feed/"),
    ("Marca Global", "https://e00-marca.uecdn.es/rss/en/index.xml"),
    ("AS English", "https://en.as.com/rss/en/football/index.xml"),
    ("OneFootball", "https://onefootball.com/en/rss"),
    ("Football365", "https://www.football365.com/feed"),
    ("Sowetan Live", "https://www.sowetanlive.co.za/sport/soccer/rss"),
    ("Daily Sun", "https://www.snl24.com/dailysun/sport/rss"),
    ("Guardian Football", "https://www.theguardian.com/football/rss"),
    ("Football Italia", "https://football-italia.net/feed/"),
    ("FourFourTwo", "https://www.fourfourtwo.com/feeds/all"),
    ("TEAMtalk", "https://www.teamtalk.com/feed"),
    ("BeSoccer", "https://www.besoccer.com/rss"),
    ("Independent", "https://www.independent.co.uk/sport/football/rss")
]

# --- AI TREND ENGINE ---
def get_3_paragraph_scout(url):
    """Deep-dives into a page to return exactly 3 social-focused paragraphs."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Extract text blocks
        paras = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 110]
        
        if len(paras) < 3:
            return "⚠️ The social scout found this topic trending, but the source content is too thin for a full report. Try another link!"

        # Constructing the 3-paragraph report
        chunk = len(paras) // 3
        p1 = " ".join(paras[:chunk])
        p2 = " ".join(paras[chunk:chunk*2])
        p3 = " ".join(paras[chunk*2:])

        report = f"### 🔥 TRENDING DEEP-DIVE REPORT\n\n"
        report += f"**📍 THE SOCIAL BUZZ:** {p1[:450]}...\n\n"
        report += f"**🔍 KEY STORY DETAILS:** {p2[:500]}...\n\n"
        report += f"**📈 TRENDING MOMENTUM:** {p3[:450]}..."
        return report
    except Exception as e:
        return f"❌ Scout Error: Could not reach the source link ({str(e)})."

def fetch_20():
    """Ensures exactly 20 unique stories are loaded."""
    results = []
    shuffled = random.sample(MASTER_POOL, len(MASTER_POOL))
    for name, url in shuffled:
        if len(results) >= 20: break
        try:
            f = feedparser.parse(url)
            if f.entries:
                results.append({'s': name, 't': f.entries[0].title, 'l': f.entries[0].link})
        except: continue
    return results

# --- APP TABS ---
tab1, tab2 = st.tabs(["📢 Global Scout Feed", "💬 Social Trend AI"])

with tab1:
    st.title("⚽ 20-SOURCE GLOBAL SCOUT")
    if st.button("🔄 REFRESH: GET 20 NEW TRENDS"):
        st.session_state.news_feed = fetch_20()

    if 'news_feed' not in st.session_state:
        st.session_state.news_feed = fetch_20()

    for i, item in enumerate(st.session_state.news_feed, 1):
        st.markdown(f'''
        <div class="news-card">
            <div class="source-tag">SOURCE {i} | {item['s']}</div>
            <a href="{item['l']}" target="_blank" class="headline-link">{item['t']}</a>
        </div>
        ''', unsafe_allow_html=True)

with tab2:
    st.header("🤖 Social Media Trends AI")
    st.caption("I scan for viral stories. Paste a link or ask for a 3-paragraph summary of any feed source!")

    # Wipe history and start fresh for Trend AI
    if "trend_messages" not in st.session_state:
        st.session_state.trend_messages = [{"role": "assistant", "content": "I am monitoring social media for trending soccer stories. Paste a URL or say 'Summarize source [number]' for a full 3-paragraph report."}]

    for msg in st.session_state.trend_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Summarize source 1 or paste link..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.trend_messages.append({"role": "user", "content": prompt})
        
        url_match = re.search(r'https?://\S+', prompt)
        
        # SCENARIO 1: User pasted a URL
        if url_match:
            with st.spinner("Analyzing social buzz for this webpage..."):
                response = get_3_paragraph_scout(url_match.group())
        
        # SCENARIO 2: User wants to summarize from the landing page feed
        elif "summarize source" in prompt.lower():
            try:
                idx = int(re.search(r'\d+', prompt).group()) - 1
                if 0 <= idx < 20:
                    target = st.session_state.news_feed[idx]
                    with st.spinner(f"Scouting {target['s']} for viral details..."):
                        response = get_3_paragraph_scout(target['l'])
                else:
                    response = "❌ Please choose a source number between 1 and 20."
            except:
                response = "❌ I didn't get that. Try 'Summarize source 1'."
        
        # SCENARIO 3: Keyword search for trends
        else:
            matches = [n for n in st.session_state.news_feed if prompt.lower() in n['t'].lower()]
            if matches:
                response = "I see this trending in today's feed. Which source should I deep-dive into?\n\n"
                for m in matches:
                    idx_label = st.session_state.news_feed.index(m) + 1
                    response += f"- **Source {idx_label}**: {m['t']}\n"
            else:
                response = "🔍 I don't see that specific trend in the current 20 stories. Paste an external link and I will break it down for you!"

        with st.chat_message("assistant"):
            st.markdown(f'<div class="summary-box">{response}</div>', unsafe_allow_html=True)
        st.session_state.trend_messages.append({"role": "assistant", "content": response})
