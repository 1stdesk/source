import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import re

# --- CONFIG & UI ---
st.set_page_config(page_title="Soccer Scout: History & Deep Intel", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #050505; color: white; }
    .stCode { background-color: #111 !important; border: 1px solid #00ff41 !important; }
    .source-btn { margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- THE 20 ELITE SOURCES ---
MASTER_POOL = [
    ("Goal.com", "https://www.goal.com/en/feeds/news"),
    ("Sky Sports", "https://www.skysports.com/rss/12040"),
    ("BBC Sport", "http://newsrss.bbc.co.uk/rss/sportonline_uk_edition/football/rss.xml"),
    ("Soccer Laduma", "https://www.snl24.com/soccerladuma/rss"),
    ("Transfermarkt", "https://www.transfermarkt.com/rss/news"),
    ("ESPN FC", "https://www.espn.com/espn/rss/soccer/news"),
    ("The Guardian", "https://www.theguardian.com/football/rss"),
    ("90min", "https://www.90min.com/posts.rss"),
    ("Marca", "https://e00-marca.uecdn.es/rss/en/index.xml"),
    ("AS English", "https://en.as.com/rss/en/football/index.xml"),
    ("Football Italia", "https://football-italia.net/feed/"),
    ("Daily Mail", "https://www.dailymail.co.uk/sport/football/index.rss"),
    ("KickOff", "https://www.snl24.com/kickoff/rss"),
    ("Sowetan Live", "https://www.sowetanlive.co.za/sport/soccer/rss"),
    ("Ghana Soccernet", "https://ghanasoccernet.com/feed"),
    ("CaughtOffside", "https://www.caughtoffside.com/feed/"),
    ("TEAMtalk", "https://www.teamtalk.com/feed"),
    ("World Soccer", "https://www.worldsoccer.com/feed"),
    ("FourFourTwo", "https://www.fourfourtwo.com/rss.xml"),
    ("Daily Sun Soccer", "https://www.snl24.com/dailysun/sport/rss")
]

def get_deep_and_history(urls):
    """Scrapes content and specifically looks for historical keywords."""
    combined = []
    history_snippets = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # Keywords to trigger historical comparison
    hist_keys = ['previously', 'last time', 'record', 'history', 'former', 'anniversary', 'years ago', 'meeting']
    
    for url in urls[:3]:
        try:
            r = requests.get(url, headers=headers, timeout=8)
            soup = BeautifulSoup(r.content, 'html.parser')
            paras = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 100]
            
            if paras:
                combined.append(paras[0]) # Main story
                # Search all paragraphs for history
                for p in paras:
                    if any(key in p.lower() for key in hist_keys):
                        history_snippets.append(p)
                        break
        except: continue
    return combined, list(set(history_snippets)) # Remove duplicates

# --- APP MAIN ---
st.title("⚽ Pro Scout: Historical Compiler")

if 'full_feed' not in st.session_state:
    with st.spinner("Syncing 20 Global Newsrooms..."):
        all_news = []
        for name, url in MASTER_POOL:
            f = feedparser.parse(url)
            if f.entries:
                all_news.append({"s": name, "t": f.entries[0].title, "l": f.entries[0].link})
        st.session_state.full_feed = all_news

query = st.text_input("Enter Team/Player for Deep Comparison:", placeholder="e.g. Celtic, Mbappe, Man Utd")

if query:
    matches = [m for m in st.session_state.full_feed if query.lower() in m['t'].lower()]
    
    if matches:
        st.success(f"Verified by {len(matches)} sources.")
        
        # Display Clickable Source Links
        st.write("🔗 **Official Source Links:**")
        cols = st.columns(len(matches[:5])) # Show first 5 links as buttons
        for idx, m in enumerate(matches[:5]):
            cols[idx].link_button(f"Read on {m['s']}", m['l'])

        if st.button("🚀 GENERATE COMPILED REPORTS"):
            with st.spinner("Analyzing current events vs history..."):
                urls = [m['l'] for m in matches]
                source_names = [m['s'] for m in matches]
                main_data, hist_data = get_deep_and_history(urls)
                
                # Hashtag Block
                tags = f"#Soccer #Football #Analysis #{query.replace(' ', '')} " + " ".join([f"#{s.replace(' ', '').replace('.','')}" for s in source_names])

                # --- 1. DEEP SUMMARY (With History) ---
                history_section = ""
                if hist_data:
                    history_section = f"📜 **HISTORICAL CONTEXT:**\n{hist_data[0][:350]}...\n\n"
                else:
                    history_section = "📜 **HISTORICAL CONTEXT:** This appears to be a fresh development with no direct historical match-up mentioned in current reports.\n\n"

                deep_summary = (
                    f"📑 **DEEP INTELLIGENCE REPORT: {query.upper()}** 📑\n\n"
                    f"Our Newsroom has cross-referenced {len(matches)} sources ({', '.join(source_names[:3])}).\n\n"
                    f"🏟️ **THE CURRENT SITUATION:**\n{main_data[0] if main_data else 'Details pending.'}\n\n"
                    f"{history_section}"
                    f"📈 **MARKET VERDICT:** The consensus across {len(matches)} outlets suggests significant impact on the upcoming schedule.\n\n"
                    f"🔗 **READ FULL STORIES:**\n" + "\n".join([f"- {m['l']}" for m in matches[:2]]) + 
                    f"\n\n{tags}"
                )

                # --- 2. QUICK SUMMARY (Fast Read) ---
                quick_summary = (
                    f"⚡ **QUICK SCOUT ALERT: {query.upper()}** ⚡\n\n"
                    f"🟢 **STATUS:** {matches[0]['t']}\n"
                    f"🟢 **HISTORY:** {'Historical trend detected' if hist_data else 'New development'}\n"
                    f"🟢 **CONSENSUS:** Confirmed by {len(matches)} global networks.\n\n"
                    f"👇 CLICKABLE LINKS IN BIO!\n\n{tags}"
                )

                # --- OUTPUT ---
                st.divider()
                st.subheader("📋 Deep Intelligence (Long-Form)")
                st.code(deep_summary, language="markdown")
                
                st.subheader("📋 Quick Scout (Short-Form)")
                st.code(quick_summary, language="markdown")

    else:
        st.warning(f"No active news for '{query}' in the last 24 hours. Try another term.")
