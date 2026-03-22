import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random

# --- CONFIG ---
st.set_page_config(page_title="Pro Insider: Respect the Work", page_icon="⚽", layout="wide")

# --- SOURCE POOL ---
SOURCES = [
    ("Soccer Laduma", "https://www.snl24.com/soccerladuma/rss"),
    ("KickOff", "https://www.snl24.com/kickoff/rss"),
    ("Goal.com", "https://www.goal.com/en/feeds/news"),
    ("Sky Sports", "https://www.skysports.com/rss/12040"),
    ("BBC Sport", "http://newsrss.bbc.co.uk/rss/sportonline_uk_edition/football/rss.xml"),
    ("Sowetan Live", "https://www.sowetanlive.co.za/sport/soccer/rss"),
    ("The South African", "https://www.thesouthafrican.com/sport/soccer/feed/"),
    ("FarPost", "https://farpost.co.za/feed/"),
    ("iDiski Times", "https://www.idiskitimes.co.za/feed/")
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
                img_url = img["content"] if img else "https://via.placeholder.com/400x225?text=Soccer+Action"
                data.append({"s": name, "t": e.title, "l": e.link, "img": img_url})
        except: continue
    return data

# --- UI ---
st.title("⚽ SOCCER HUB: REAL TALK EDITION")

if 'visual_feed' not in st.session_state:
    st.session_state.visual_feed = fetch_next_20()

m_col, s_col = st.columns([4, 1.2])

with m_col:
    grid = st.columns(4)
    for idx, item in enumerate(st.session_state.visual_feed):
        with grid[idx % 4]:
            st.markdown(f'''
                <div style="background:#111; border-radius:10px; border:1px solid #333; margin-bottom:10px; height:380px; overflow:hidden;">
                    <img src="{item['img']}" style="width:100%; height:160px; object-fit:cover;">
                    <div style="padding:10px;">
                        <p style="color:#00ff41; font-size:10px; font-weight:bold; margin:0;">{item['s'].upper()}</p>
                        <p style="font-size:13px; font-weight:bold; color:white; margin-top:5px; height:50px; overflow:hidden;">{item['t']}</p>
                        <a href="{item['l']}" target="_blank" style="color:#888; font-size:11px; text-decoration:none;">🔗 Official Source</a>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            if st.button("🎤 GENERATE SCOOP", key=f"btn_{idx}", use_container_width=True):
                st.session_state.active = item

with s_col:
    st.markdown("### 🔥 Trending Context")
    for t in ["#Amakhosi", "#RespectTheWork", "#PSLUpdates", "#DStvPrem"]:
        st.markdown(f'<div style="background:#111; padding:10px; border-radius:8px; margin-bottom:8px; border-left:3px solid #00ff41; color:white; font-size:14px;">{t}</div>', unsafe_allow_html=True)
    if st.button("🔄 REFRESH: NEW SOURCES", use_container_width=True):
        st.session_state.visual_feed = fetch_next_20()
        st.rerun()

# --- THE "REAL TALK" GENERATOR ---
if 'active' in st.session_state:
    it = st.session_state.active
    st.divider()
    
    # Cleaning title for a more natural flow
    clean_title = it['t'].split('-')[0].strip()
    source_tag = f"#{it['s'].replace(' ', '')}"
    
    # THE SCOOP (Following your specific style)
    real_talk_scoop = (
        f"We always find something to say about **{it['s']}** and their latest news... but let’s be honest for a second 🗣️\n\n"
        f"Every time they hit the headlines with stories like **\"{clean_title}\"**, the results on the pitch speak for themselves! 📈\n\n"
        f"Maybe it’s time we give credit where it’s due. Solid, reliable, and always stepping up when the pressure is at its highest! 💎\n\n"
        f"Respect the silent work and the consistency! 🛡️\n\n"
        f"👇 **READ THE FULL STORY:**\n"
        f"{it['l']}\n\n"
        f"{source_tag} #FootballNews #RespectTheWork #GameChanger #SoccerUpdate"
    )

    st.subheader(f"🎤 Real Talk Scoop for: {it['s']}")
    st.code(real_talk_scoop, language="markdown")
