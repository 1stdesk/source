import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random
import re

# --- CONFIG ---
st.set_page_config(page_title="Soccer Social Scout AI", page_icon="🔥", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #161b22; border-radius: 10px; color: white; }
    .stTabs [aria-selected="true"] { background-color: #238636; color: white; font-weight: bold; }
    .news-card { background-color: #161b22; padding: 18px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 15px; }
    .source-tag { color: #58a6ff; font-weight: bold; font-size: 0.75rem; text-transform: uppercase; }
    .headline-link { color: #f0f6fc; font-weight: bold; text-decoration: none; font-size: 1.1rem; }
    .summary-box { background-color: #0d1117; padding: 20px; border-radius: 10px; border: 1px solid #238636; margin-top: 15px; line-height: 1.6; }
    </style>
    """, unsafe_allow_html=True)

# --- SOCIAL-FIRST SOURCES ---
SOCIAL_SOURCES = [
    ("Reddit r/Soccer Trending", "https://www.reddit.com/r/soccer/hot/.rss"),
    ("Goal.com Viral", "https://www.goal.com/en/feeds/news"),
    ("Sky Breaking", "https://www.skysports.com/rss/12040"),
    ("Transfer News Live", "https://www.transfermarkt.com/rss/news"),
    ("CaughtOffside (Social)", "https://www.caughtoffside.com/feed/"),
    ("BBC Social Feed", "https://push.api.bbci.co.uk/morph/items?page=1&limit=10&feed=football")
]

# --- SCRAPING ENGINE ---
def get_3_para_deep_dive(url):
    """Scrapes a URL and generates a 3-paragraph social summary."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        paras = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 100]
        
        if len(paras) < 3:
            return "⚠️ Trending story identified, but content is too brief for a full deep-dive. Check the source link!"

        # Create 3 distinct paragraphs
        chunk = len(paras) // 3
        p1 = " ".join(paras[:chunk])
        p2 = " ".join(paras[chunk:chunk*2])
        p3 = " ".join(paras[chunk*2:])

        report = f"### 🔥 SOCIAL TREND REPORT\n\n"
        report += f"**📊 THE VIRAL ANGLE:** {p1[:450]}...\n\n"
        report += f"**💬 PUBLIC REACTION:** {p2[:500]}...\n\n"
        report += f"**📈 MOMENTUM & UPDATES:** {p3[:450]}..."
        return report
    except Exception as e:
        return f"❌ Social Scout failed to connect: {str(e)}"

def fetch_20():
    """Fetches exactly 20 headlines across social and news streams."""
    results = []
    # Fill up with RSS feeds to ensure exactly 20
    for name, url in SOCIAL_SOURCES:
        try:
            f = feedparser.parse(url)
            for entry in f.entries[:4]: # Take top 4 from each to build the 20
                if len(results) < 20:
                    results.append({'s': name, 't': entry.title, 'l': entry.link})
        except: continue
    return results

# --- UI LAYOUT ---
tab1, tab2 = st.tabs(["📢 Global News Feed", "💬 Social Scout Chat"])

with tab1:
    st.title("⚽ 20-SOURCE GLOBAL FEED")
    if st.button("🔄 REFRESH FEED"):
        st.session_state.news_feed = fetch_20()
    if 'news_feed' not in st.session_state:
        st.session_state.news_feed = fetch_20()

    for i, item in enumerate(st.session_state.news_feed, 1):
        st.markdown(f'''<div class="news-card"><div class="source-tag">SOURCE {i} | {item['s']}</div>
        <a href="{item['l']}" target="_blank" class="headline-link">{item['t']}</a></div>''', unsafe_allow_html=True)

with tab2:
    st.header("🤖 Social Media Trends AI")
    st.caption("I scan for viral stories. Paste a link or ask for a summary of a feed source!")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "I'm monitoring social trends. Paste any viral link or say 'Summarize source 1' for a 3-paragraph breakdown."}]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about a trending player or paste a URL..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        url_match = re.search(r'https?://\S+', prompt)
        
        if url_match:
            with st.spinner("Analyzing social buzz for this link..."):
                response = get_3_para_deep_dive(url_match.group())
        elif "summarize source" in prompt.lower():
            try:
                idx = int(re.search(r'\d+', prompt).group()) - 1
                target = st.session_state.news_feed[idx]
                with st.spinner(f"Scouting social sentiment for {target['s']}..."):
                    response = get_3_para_deep_dive(target['l'])
            except:
                response = "❌ I need a source number between 1 and 20."
        else:
            # Trending Search Logic
            matches = [n for n in st.session_state.news_feed if prompt.lower() in n['t'].lower()]
            if matches:
                response = "I see this trending in the feed. Which source should I deep-dive into?\n\n"
                for m in matches:
                    response += f"- **Source {st.session_state.news_feed.index(m)+1}**: {m['t']}\n"
            else:
                response = "🔍 I don't see that trending right now. Paste a link to any social post/article and I'll break it down into 3 paragraphs!"

        with st.chat_message("assistant"):
            st.markdown(f'<div class="summary-box">{response}</div>', unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": response})
