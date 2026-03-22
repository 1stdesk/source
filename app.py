import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random

# --- CONFIG ---
st.set_page_config(page_title="Pro Soccer Insider", page_icon="⚽", layout="wide")

# --- SOURCE POOL ---
SOURCES = [
    ("Goal.com", "https://www.goal.com/en/feeds/news"), ("Sky Sports", "https://www.skysports.com/rss/12040"),
    ("BBC Sport", "http://newsrss.bbc.co.uk/rss/sportonline_uk_edition/football/rss.xml"), ("Transfermarkt", "https://www.transfermarkt.com/rss/news"),
    ("ESPN FC", "https://www.espn.com/espn/rss/soccer/news"), ("The Guardian", "https://www.theguardian.com/football/rss"),
    ("Marca", "https://e00-marca.uecdn.es/rss/en/index.xml"), ("Football Italia", "https://football-italia.net/feed/"),
    ("The Athletic", "https://theathletic.com/rss"), ("CaughtOffside", "https://www.caughtoffside.com/feed/"),
    ("Barca Universal", "https://barcauniversal.com/feed/"), ("This Is Anfield", "https://www.thisisanfield.com/feed/")
]

# --- QUEUE SYSTEM ---
if 'source_queue' not in st.session_state:
    all_s = SOURCES.copy()
    random.shuffle(all_s)
    st.session_state.source_queue = all_s
    st.session_state.queue_index = 0

def fetch_next_20():
    if st.session_state.queue_index + 20 > len(st.session_state.source_queue):
        random.shuffle(st.session_state.source_queue)
        st.session_state.queue_index = 0
    selected = st.session_state.source_queue[st.session_state.queue_index : st.session_state.queue_index + 20]
    st.session_state.queue_index += 20
    
    data = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    for name, url in selected:
        try:
            f = feedparser.parse(url)
            if f.entries:
                e = f.entries[0]
                r = requests.get(e.link, headers=headers, timeout=1.5)
                soup = BeautifulSoup(r.content, 'html.parser')
                img = soup.find("meta", property="og:image")
                img_url = img["content"] if img else "https://via.placeholder.com/400x225?text=Breaking+News"
                data.append({"s": name, "t": e.title, "l": e.link, "img": img_url})
        except: continue
    return data

def generate_insider_summary(url):
    """Scrapes the article to create a context-heavy summary."""
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=3)
        soup = BeautifulSoup(r.content, 'html.parser')
        # Grab first 3 substantial paragraphs for context
        paras = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 80]
        if len(paras) >= 2:
            return f"{paras[0][:250]}... Additionally, reports suggest {paras[1][:200]}..."
        return paras[0] if paras else "No deeper context found; primary report at source link."
    except:
        return "Tactical details are being updated in real-time."

# --- UI ---
st.title("⚽ PRO SOCCER INSIDER")
st.caption(f"Source Cycle: {st.session_state.queue_index}/{len(SOURCES)}")

if 'visual_feed' not in st.session_state:
    st.session_state.visual_feed = fetch_next_20()

m_col, s_col = st.columns([4, 1.2])

with m_col:
    grid = st.columns(4)
    for idx, item in enumerate(st.session_state.visual_feed):
        with grid[idx % 4]:
            st.markdown(f'''
                <div style="background:#111; border-radius:10px; border:1px solid #333; margin-bottom:10px; height:370px; overflow:hidden;">
                    <img src="{item['img']}" style="width:100%; height:160px; object-fit:cover;">
                    <div style="padding:8px;">
                        <p style="color:#00ff41; font-size:10px; font-weight:bold; margin:0;">{item['s'].upper()}</p>
                        <p style="font-size:12px; font-weight:bold; color:white; margin-top:4px; height:50px; overflow:hidden;">{item['t']}</p>
                        <a href="{item['l']}" target="_blank" style="color:#888; font-size:10px;">🔗 View Original</a>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            if st.button("🎤 DEEP SUMMARY", key=f"gen_{idx}", use_container_width=True):
                st.session_state.active = item

with s_col:
    st.markdown("### 🔥 Market Trends")
    for t in ["#HereWeGo", "#TransferMarket", "#FFP", "#UCL"]:
        st.markdown(f'<div style="background:#222; padding:8px; border-radius:5px; margin-bottom:5px; border-left:3px solid #00ff41; font-size:12px;">{t}</div>', unsafe_allow_html=True)
    if st.button("🔄 REFRESH FEED", use_container_width=True):
        st.session_state.visual_feed = fetch_next_20()
        st.rerun()

# --- THE SUMMARY ENGINE ---
if 'active' in st.session_state:
    it = st.session_state.active
    st.divider()
    with st.spinner("Analyzing tactical radiography..."):
        context_summary = generate_insider_summary(it['l'])
        
        # PRO CONTENT TEMPLATE
        insider_post = (
            f"📰 **THE DEEP SCOOP: {it['t'].upper()}**\n"
            f"**\"HERE WE GO\" ENERGY — MARKET ANALYSIS**\n\n"
            f"🏆 **THE BREAKDOWN:**\n"
            f"Understand the move: Reporting via **{it['s']}**, this is more than just a headline. We are seeing a strategic shift as clubs look to navigate Financial Fair Play while securing top-tier talent.\n\n"
            f"⚽ **INSIDER SUMMARY:**\n"
            f"{context_summary}\n\n"
            f"📈 **MARKET VERDICT:**\n"
            f"This is a statement of intent. Whether it's a swap deal or a direct buy, the tactical ceiling of the squad changes today. This is the move fans have been waiting for. 💎\n\n"
            f"👇 **FULL RADIOGRAPHY & SOURCE:**\n"
            f"{it['l']}\n\n"
            f"What’s your take on this strategy? 👇 #{it['s'].replace(' ', '')} #FootballNews #FabrizioEnergy #Soccer"
        )
        
        st.subheader("Insider Deep Scoop")
        st.code(insider_post, language="markdown")
