import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random

# --- CONFIG ---
st.set_page_config(page_title="Ultra Soccer Scout + Hashtags", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #050505; }
    .news-card { 
        background-color: #121212; 
        padding: 20px; 
        border-radius: 15px; 
        border: 1px solid #333; 
        margin-bottom: 20px;
    }
    .hashtag-pill {
        color: #00ff41;
        background-color: #002b0b;
        padding: 4px 10px;
        border-radius: 15px;
        font-size: 0.85rem;
        font-weight: bold;
        display: inline-block;
        margin-right: 5px;
        margin-top: 5px;
        border: 1px solid #00ff41;
    }
    .source-tag { color: #00ff41; font-weight: bold; font-size: 0.8rem; text-transform: uppercase; }
    .summary-box { color: #d1d1d1; font-size: 0.95rem; background-color: #000; padding: 15px; border-radius: 10px; margin-top: 10px; border-left: 3px solid #00ff41; }
    .headline-link { color: white; font-weight: bold; text-decoration: none; font-size: 1.2rem; }
    </style>
    """, unsafe_allow_html=True)

# --- SOURCES ---
MASTER_POOL = [
    ("Goal.com", "https://www.goal.com/en/feeds/news"),
    ("ESPN FC", "https://www.espn.com/espn/rss/soccer/news"),
    ("Sky Sports", "https://www.skysports.com/rss/12040"),
    ("BBC Sport", "https://push.api.bbci.co.uk/morph/items?page=1&limit=10&feed=football"),
    ("The Guardian", "https://www.theguardian.com/football/rss"),
    ("OneFootball", "https://onefootball.com/en/rss"),
    ("Soccer Laduma", "https://www.snl24.com/soccerladuma/rss"),
    ("KickOff", "https://www.snl24.com/kickoff/rss"),
    ("Transfermarkt", "https://www.transfermarkt.com/rss/news"),
    ("90min", "https://www.90min.com/posts.rss"),
    ("CaughtOffside", "https://www.caughtoffside.com/feed/"),
    ("Marca", "https://e00-marca.uecdn.es/rss/en/index.xml"),
    ("AS English", "https://en.as.com/rss/en/football/index.xml")
]

def generate_hashtags(source_name, title):
    """Generates trending and relevant hashtags."""
    base_tags = ["#soccer", "#football", "#futbol", "#2026", "#transfernews"]
    
    # Source-specific tag
    clean_source = source_name.replace(" ", "").replace(".com", "")
    source_tag = f"#{clean_source}"
    
    # Simple logic to add club/league tags if found in title
    extra_tags = []
    if "United" in title: extra_tags.append("#MUFC")
    if "City" in title: extra_tags.append("#MCFC")
    if "Arsenal" in title: extra_tags.append("#Arsenal")
    if "Liverpool" in title: extra_tags.append("#LFC")
    if "Madrid" in title: extra_tags.append("#RealMadrid")
    if "Champions League" in title: extra_tags.append("#UCL")
    
    # Combine and shuffle a few
    all_tags = list(set(base_tags + [source_tag] + extra_tags))
    return random.sample(all_tags, min(len(all_tags), 6))

def scout_article(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=7)
        soup = BeautifulSoup(r.content, 'html.parser')
        img = soup.find("meta", property="og:image")
        paras = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 100]
        return {"img": img["content"] if img else None, "text": " ".join(paras[:2])}
    except:
        return None

def get_fresh_20():
    shuffled = list(MASTER_POOL)
    random.shuffle(shuffled)
    news = []
    for name, url in shuffled:
        if len(news) >= 20: break
        try:
            f = feedparser.parse(url)
            if f.entries:
                news.append({'s': name, 't': f.entries[0].title, 'l': f.entries[0].link})
        except: continue
    return news

# --- UI ---
st.title("⚽ ULTRA SCOUT + TRENDING TAGS")

if st.button("🔄 REFRESH GLOBAL FEED"):
    st.session_state.feed = get_fresh_20()

if 'feed' not in st.session_state:
    st.session_state.feed = get_fresh_20()

for i, item in enumerate(st.session_state.feed, 1):
    st.markdown(f'<div class="news-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="source-tag">{i}. {item["s"]}</div>', unsafe_allow_html=True)
    st.markdown(f'<a href="{item["l"]}" target="_blank" class="headline-link">{item["t"]}</a>', unsafe_allow_html=True)
    
    if st.button(f"🧠 AI REPORT & HASHTAGS #{i}", key=f"btn_{i}"):
        with st.spinner("Scouting..."):
            data = scout_article(item['l'])
            tags = generate_hashtags(item['s'], item['t'])
            
            if data:
                c1, c2 = st.columns([1, 2])
                with c1:
                    if data['img']:
                        st.image(data['img'], use_container_width=True)
                with c2:
                    st.markdown(f'<div class="summary-box"><b>SCOUT SUMMARY:</b><br>{data["text"]}</div>', unsafe_allow_html=True)
                    # Display Hashtags
                    st.write("---")
                    st.markdown("**TRENDING HASHTAGS:**")
                    tag_html = "".join([f'<span class="hashtag-pill">{t}</span>' for t in tags])
                    st.markdown(tag_html, unsafe_allow_html=True)
            else:
                st.warning("Could not extract summary.")
    st.markdown('</div>', unsafe_allow_html=True)
