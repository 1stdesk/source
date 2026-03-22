import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random
import re

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
    .summary-box { 
        background-color: #1a1a1a; padding: 20px; border-radius: 10px; 
        border-left: 5px solid #00ff41; margin-top: 10px;
    }
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
    ("The Guardian", "https://www.theguardian.com/football/rss"),
    ("90min", "https://www.90min.com/posts.rss"),
    ("Transfermarkt", "https://www.transfermarkt.com/rss/news"),
    ("Marca", "https://e00-marca.uecdn.es/rss/en/index.xml")
]

# --- SCRAPING ENGINE ---
def get_deep_summary(url):
    """Scrapes a URL and returns a 3-paragraph summary."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Extract main text paragraphs
        paragraphs = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 100]
        
        if len(paragraphs) < 3:
            return "⚠️ I couldn't find enough text on that page to make a full report. It might be protected or have too little content."

        # Logic to split into 3 distinct sections
        chunk = len(paragraphs) // 3
        p1 = " ".join(paragraphs[:chunk])
        p2 = " ".join(paragraphs[chunk:chunk*2])
        p3 = " ".join(paragraphs[chunk*2:])

        report = f"### 📄 AI SCOUT DEEP-DIVE REPORT\n\n"
        report += f"**📍 THE LEAD:** {p1[:450]}...\n\n"
        report += f"**🔍 THE DETAILS:** {p2[:500]}...\n\n"
        report += f"**🏁 THE VERDICT:** {p3[:450]}..."
        return report
    except Exception as e:
        return f"❌ Error: Could not connect to the site. ({str(e)})"

def fetch_20():
    """Picks 20 random sources and gets 1 story from each."""
    random_sources = random.sample(MASTER_POOL, min(len(MASTER_POOL), 20))
    results = []
    for name, url in random_sources:
        try:
            f = feedparser.parse(url)
            if f.entries:
                results.append({'s': name, 't': f.entries[0].title, 'l': f.entries[0].link})
        except: continue
    return results

# --- APP LAYOUT ---
tab1, tab2 = st.tabs(["📢 Global Scout Feed", "💬 Chat with AI Scout"])

with tab1:
    st.title("⚽ ULTRA SOCCER AGGREGATOR")
    if st.button("🔄 REFRESH: SCAN NEW SOURCES"):
        st.session_state.news_feed = fetch_20()

    if 'news_feed' not in st.session_state:
        st.session_state.news_feed = fetch_20()

    for i, item in enumerate(st.session_state.news_feed, 1):
        st.markdown(f'''
        <div class="news-card">
            <div class="source-tag">{i}. {item['s']}</div>
            <a href="{item['l']}" target="_blank" class="headline-link">{item['t']}</a>
        </div>
        ''', unsafe_allow_html=True)

with tab2:
    st.header("🤖 Web Summarizer Assistant")
    st.caption("Paste any URL or type 'Summarize source 1' to get a 3-paragraph report!")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "I am ready. Paste a link or ask about the current feed!"}]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Paste a link or say 'Summarize source 1'"):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # LOGIC 1: Detect if user pasted a direct URL
        url_match = re.search(r'https?://\S+', prompt)
        
        if url_match:
            target_url = url_match.group()
            with st.spinner("Scraping webpage for a 3-paragraph summary..."):
                response = get_deep_summary(target_url)
        
        # LOGIC 2: Detect "Summarize source X" command
        elif "summarize source" in prompt.lower():
            try:
                idx = int(prompt.lower().split("source")[-1].strip()) - 1
                target_url = st.session_state.news_feed[idx]['l']
                with st.spinner(f"Analyzing {st.session_state.news_feed[idx]['s']}..."):
                    response = get_deep_summary(target_url)
            except:
                response = "❌ Please provide a valid source number (e.g., 'Summarize source 1')."
        
        # LOGIC 3: General Keyword Search
        else:
            matches = [n for n in st.session_state.news_feed if prompt.lower() in n['t'].lower()]
            if matches:
                response = "I found these stories. Which one should I summarize for you?\n\n"
                for m in matches:
                    response += f"- **{m['s']}**: {m['t']}\n"
            else:
                response = "🔍 I couldn't find a specific match. Paste a link directly if you want me to summarize an external page!"

        with st.chat_message("assistant"):
            st.markdown(f'<div class="summary-box">{response}</div>', unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": response})
