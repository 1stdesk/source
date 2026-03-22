import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random

# --- CONFIG ---
st.set_page_config(page_title="Football AI Monitor 2026", page_icon="⚽", layout="wide")

# Custom CSS for that "Matrix/Dark" look
st.markdown("""
    <style>
    .main { background-color: #050505; }
    .stButton>button { background-color: #00ff41; color: black; font-weight: bold; width: 100%; border: none; }
    .news-card {
        background-color: #121212;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #333;
        margin-bottom: 15px;
    }
    .source-tag { color: #00ff41; font-size: 0.8rem; font-weight: bold; margin-bottom: 5px; }
    .summary-text { color: #d1d1d1; font-size: 0.95rem; line-height: 1.5; margin: 10px 0; }
    .headline { color: white; font-size: 1.2rem; font-weight: bold; text-decoration: none; display: block; }
    .headline:hover { color: #00ff41; }
    </style>
    """, unsafe_allow_html=True)

MASTER_SOURCES = [
    ("Soccer Laduma", "https://www.snl24.com/soccerladuma/rss"),
    ("KickOff", "https://www.snl24.com/kickoff/rss"),
    ("Daily Sun Sport", "https://www.snl24.com/dailysun/sport/rss"),
    ("SuperSport", "https://supersport.com/rss/football"),
    ("Sowetan Live", "https://www.sowetanlive.co.za/sport/soccer/rss"),
    ("BBC Football", "https://push.api.bbci.co.uk/morph/items?page=1&limit=10&feed=football"),
    ("Sky Sports", "https://www.skysports.com/rss/12040"),
    ("The Guardian", "https://www.theguardian.com/football/rss"),
    ("Goal.com", "https://www.goal.com/en/feeds/news"),
    ("Transfermarkt", "https://www.transfermarkt.com/rss/news"),
    ("Marca (Spain)", "https://e00-marca.uecdn.es/rss/en/index.xml"),
    ("AS (Spain)", "https://en.as.com/rss/en/football/index.xml"),
    ("Google News: PSL", "https://news.google.com/rss/search?q=PSL+football+when:1h&hl=en-ZA&gl=ZA"),
    ("Google News: Transfers", "https://news.google.com/rss/search?q=football+transfers+when:1h&hl=en-ZA&gl=ZA")
]

def get_article_details(url):
    """Scrapes the article for the main image and a text summary."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Image extraction (Look for OpenGraph image first)
        img_tag = soup.find("meta", property="og:image")
        img_url = img_tag["content"] if img_tag else None
        
        # Summary extraction (First 3 significant paragraphs)
        paras = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60]
        summary = " ".join(paras[:3])
        
        return {"img": img_url, "summary": summary}
    except:
        return None

def fetch_news():
    shuffled_pool = list(MASTER_SOURCES)
    random.shuffle(shuffled_pool)
    headers = {'User-Agent': 'Mozilla/5.0'}
    news_to_show = []
    
    for name, url in shuffled_pool:
        if len(news_to_show) >= 15: break # Reduced to 15 for better stability
        try:
            r = requests.get(url, headers=headers, timeout=5)
            f = feedparser.parse(r.content)
            for e in f.entries[:1]: # Take 1 per source for maximum variety
                news_to_show.append({'s': name, 't': e.title.rsplit(' - ', 1)[0], 'l': e.link})
        except: continue
    return news_to_show

# --- UI LAYOUT ---
st.title("⚽ DYNAMIC AI MONITOR")

if st.button("🔄 REFRESH GLOBAL SCOUT"):
    st.session_state.news_items = fetch_news()

if 'news_items' not in st.session_state:
    st.session_state.news_items = fetch_news()

# Displaying Feed
for idx, item in enumerate(st.session_state.news_items, 1):
    with st.container():
        st.markdown(f'<div class="source-tag">{idx}. {item["s"].upper()}</div>', unsafe_allow_html=True)
        st.markdown(f'<a class="headline" href="{item["l"]}" target="_blank">{item["t"]}</a>', unsafe_allow_html=True)
        
        # The AI Processor Button
        if st.button(f"🧠 Summarize & Grab Image #{idx}", key=f"btn_{idx}"):
            with st.spinner("Extracting data..."):
                details = get_article_details(item['l'])
                if details:
                    col_img, col_txt = st.columns([1, 2])
                    with col_img:
                        if details['img']:
                            st.image(details['img'], use_container_width=True)
                            img_data = requests.get(details['img']).content
                            st.download_button("💾 Download Image", img_data, f"football_img_{idx}.jpg", "image/jpeg")
                    with col_txt:
                        st.markdown(f'<div class="summary-text">{details["summary"]}</div>', unsafe_allow_html=True)
                else:
                    st.error("Site blocked our scout or no content found.")
        st.markdown("---")
