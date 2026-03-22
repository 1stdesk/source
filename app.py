import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random
import re

# --- CONFIG & STYLING ---
st.set_page_config(page_title="20-Source Soccer AI Scout", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #050505; color: white; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; background-color: #121212; border-radius: 10px; color: white; 
    }
    .stTabs [aria-selected="true"] { background-color: #00ff41; color: black; font-weight: bold; }
    .news-card { 
        background-color: #121212; padding: 18px; border-radius: 12px; 
        border: 1px solid #333; margin-bottom: 15px;
    }
    .source-tag { color: #00ff41; font-weight: bold; font-size: 0.75rem; text-transform: uppercase; margin-bottom: 5px; }
    .headline-link { color: white; font-weight: bold; text-decoration: none; font-size: 1.1rem; line-height: 1.2; }
    .headline-link:hover { color: #00ff41; }
    .summary-box { 
        background-color: #1a1a1a; padding: 20px; border-radius: 10px; 
        border-left: 5px solid #00ff41; margin-top: 10px; color: #eee;
    }
    </style>
    """, unsafe_allow_html=True)

# --- EXPANDED SOURCE POOL (From your provided list) ---
# We use RSS feeds for these to ensure we get the latest headlines instantly
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
    ("Marca", "https://e00-marca.uecdn.es/rss/en/index.xml"),
    ("AS English", "https://en.as.com/rss/en/football/index.xml"),
    ("FourFourTwo", "https://www.fourfourtwo.com/feeds/all"),
    ("TEAMtalk", "https://www.teamtalk.com/feed"),
    ("Football365", "https://www.football365.com/feed"),
    ("CaughtOffside", "https://www.caughtoffside.com/feed/"),
    ("OneFootball", "https://onefootball.com/en/rss"),
    ("BeSoccer", "https://www.besoccer.com/rss"),
    ("Football Italia", "https://football-italia.net/feed/"),
    ("Sowetan Live", "https://www.sowetanlive.co.za/sport/soccer/rss"),
    ("Daily Sun", "https://www.snl24.com/dailysun/sport/rss"),
    ("Mirror Football", "https://www.mirror.co.uk/sport/football/rss.xml"),
    ("Independent", "https://www.independent.co.uk/sport/football/rss"),
    ("Daily Mail", "https://www.dailymail.co.uk/sport/football/index.rss"),
    ("Evening Standard", "https://www.standard.co.uk/sport/football/rss")
]

# --- SCRAPING & FETCHING ENGINE ---
def get_deep_summary(url):
    """Scrapes a URL and returns a 3-paragraph summary."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        paragraphs = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 100]
        
        if len(paragraphs) < 3:
            return "⚠️ Not enough content found to build a 3-paragraph report. Try a different source."

        chunk = len(paragraphs) // 3
        p1 = " ".join(paragraphs[:chunk])
        p2 = " ".join(paragraphs[chunk:chunk*2])
        p3 = " ".join(paragraphs[chunk*2:])

        report = f"### 📄 AI SCOUT DEEP-DIVE\n\n"
        report += f"**1. THE SITUATION:** {p1[:450]}...\n\n"
        report += f"**2. KEY DETAILS:** {p2[:500]}...\n\n"
        report += f"**3. FUTURE OUTLOOK:** {p3[:450]}..."
        return report
    except Exception as e:
        return f"❌ Error connecting to source: {str(e)}"

def fetch_20():
    """Fetches exactly 20 unique stories from random sources in the pool."""
    shuffled_sources = random.sample(MASTER_POOL, len(MASTER_POOL))
    results = []
    
    for name, url in shuffled_sources:
        if len(results) >= 20: break # Stop exactly at 20
        try:
            f = feedparser.parse(url)
            if f.entries:
                results.append({'s': name, 't': f.entries[0].title, 'l': f.entries[0].link})
        except: continue
    return results

# --- APP UI ---
tab1, tab2 = st.tabs(["📢 Global Scout Feed", "💬 Chat with AI Scout"])

with tab1:
    st.title("⚽ 20-SOURCE GLOBAL SCOUT")
    st.subheader("Your AI-powered football intelligence center")
    
    if st.button("🔄 REFRESH: SCAN 20 NEW SOURCES"):
        st.session_state.news_feed = fetch_20()

    if 'news_feed' not in st.session_state:
        st.session_state.news_feed = fetch_20()

    # Display 20 news cards
    for i, item in enumerate(st.session_state.news_feed, 1):
        st.markdown(f'''
        <div class="news-card">
            <div class="source-tag">SOURCE {i} | {item['s']}</div>
            <a href="{item['l']}" target="_blank" class="headline-link">{item['t']}</a>
        </div>
        ''', unsafe_allow_html=True)

with tab2:
    st.header("🤖 AI Scout & Web Summarizer")
    st.caption("Ask me to 'Summarize source 14' or paste any URL for a 3-paragraph report!")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Welcome back! I have analyzed the 20 sources on your landing page. How can I help?"}]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Paste a link or say 'Summarize source 1'"):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        url_match = re.search(r'https?://\S+', prompt)
        
        if url_match:
            target_url = url_match.group()
            with st.spinner("Analyzing website for a 3-paragraph summary..."):
                response = get_deep_summary(target_url)
        
        elif "summarize source" in prompt.lower():
            try:
                # Extract the number from the prompt
                idx = int(re.search(r'\d+', prompt).group()) - 1
                if 0 <= idx < 20:
                    target_url = st.session_state.news_feed[idx]['l']
                    source_name = st.session_state.news_feed[idx]['s']
                    with st.spinner(f"Scouting {source_name}..."):
                        response = get_deep_summary(target_url)
                else:
                    response = "❌ Please pick a number between 1 and 20."
            except:
                response = "❌ I didn't catch that number. Try 'Summarize source 1'."
        
        else:
            # Keyword search through the 20 sources
            matches = [n for n in st.session_state.news_feed if prompt.lower() in n['t'].lower()]
            if matches:
                response = "I found these stories in your current feed. Ask me to 'Summarize source [number]' for a report:\n\n"
                for m in matches:
                    idx_in_feed = st.session_state.news_feed.index(m) + 1
                    response += f"- **Source {idx_in_feed} ({m['s']})**: {m['t']}\n"
            else:
                response = "🔍 I couldn't find that in the 20 stories. You can paste any external link here and I will summarize it for you!"

        with st.chat_message("assistant"):
            st.markdown(f'<div class="summary-box">{response}</div>', unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": response})
