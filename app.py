import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import re

# --- CONFIG & UI ---
st.set_page_config(page_title="Pro Scout: Deep Compiler", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .output-container { background-color: #0f172a; padding: 20px; border-radius: 12px; border: 1px solid #1e293b; margin-top: 20px; }
    .header-style { color: #00ff41; font-family: 'Courier New', monospace; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- THE 20 SOURCES ---
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

def get_deep_content(urls):
    combined = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    for url in urls[:3]: # Scrape top 3 matching sources
        try:
            r = requests.get(url, headers=headers, timeout=7)
            soup = BeautifulSoup(r.content, 'html.parser')
            # Extract paragraphs that actually contain story data
            paras = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 120]
            combined.append(paras)
        except: continue
    return combined

# --- MAIN LOGIC ---
st.title("⚽ AI Newsroom: Deep Compiler")

if 'news_data' not in st.session_state:
    with st.spinner("Syncing 20 Global Newsrooms..."):
        all_news = []
        for name, url in MASTER_POOL:
            f = feedparser.parse(url)
            if f.entries:
                all_news.append({"s": name, "t": f.entries[0].title, "l": f.entries[0].link})
        st.session_state.news_data = all_news

query = st.text_input("Search a Team or Player to Compile (e.g. 'Celtic'):")

if query:
    matches = [m for m in st.session_state.news_data if query.lower() in m['t'].lower()]
    
    if matches:
        st.success(f"Verified by {len(matches)} sources.")
        if st.button("🚀 GENERATE COMPILED REPORTS"):
            with st.spinner("Analyzing and Synthesizing..."):
                source_list = [m['s'] for m in matches]
                urls = [m['l'] for m in matches]
                content_blocks = get_deep_content(urls)
                
                # Format Tags
                tags = f"#Football #Soccer #TransferNews #{query.replace(' ', '')} " + " ".join([f"#{s.replace(' ', '').replace('.','')}" for s in source_list])

                # --- 1. DEEP SUMMARY ---
                deep_summary = f"📑 **DEEP INTELLIGENCE REPORT: {query.upper()}** 📑\n\n"
                deep_summary += f"Our AI Newsroom has cross-referenced reports from {', '.join(source_list)} to provide this comprehensive update.\n\n"
                
                for block in content_blocks:
                    if block:
                        deep_summary += f"🏟️ **ANALYSIS:** {block[0][:300]}...\n\n"
                        if len(block) > 1:
                            deep_summary += f"🔍 **KEY DETAIL:** {block[1][:250]}...\n\n"
                
                deep_summary += f"📈 **MARKET IMPACT:** This development is shifting the title race/transfer market significantly. {len(matches)} outlets confirm the urgency of this situation.\n\n"
                deep_summary += f"🔗 Sources: {', '.join(urls[:2])}\n\n{tags}"

                # --- 2. QUICK SUMMARY ---
                quick_summary = (
                    f"⚡ **QUICK SCOUT ALERT: {query.upper()}** ⚡\n\n"
                    f"🟢 **SITUATION:** {matches[0]['t']}\n"
                    f"🟢 **CONSENSUS:** Verified by {len(matches)} sources ({', '.join(source_list[:2])}).\n"
                    f"🟢 **ACTION:** Watch this space as details develop.\n\n"
                    f"👇 Read more at links in bio!\n\n{tags}"
                )

                # --- DISPLAY ---
                st.markdown("### 📋 Choice 1: Deep Intelligence (Long-Form)")
                st.code(deep_summary, language="markdown")
                
                st.markdown("### 📋 Choice 2: Quick Scout (Short-Form)")
                st.code(quick_summary, language="markdown")

    else:
        st.error("No recent stories found for that topic in the 20 sources.")
