import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import hashlib
import pandas as pd

# --- CONFIG ---
st.set_page_config(page_title="Soccer Scout AI v3", page_icon="⚽", layout="wide")

# --- AI SETUP (Cached to prevent reloading) ---
@st.cache_resource
def load_summarizer():
    # Using a fast, distilled model perfect for cloud hosting
    return pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

summarizer = load_summarizer()

# --- SCRAPER LOGIC ---
class SoccerScraper:
    def __init__(self, sources_file="sources.txt"):
        try:
            with open(sources_file, "r") as f:
                self.sources = [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            self.sources = ["https://www.goal.com/en/feeds/news"] # Fallback

    def get_content(self, url):
        try:
            r = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(r.content, 'html.parser')
            # Extract high-res image
            img_tag = soup.find("meta", property="og:image")
            img = img_tag["content"] if img_tag else None
            # Extract text
            paras = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 50]
            text = " ".join(paras[:3])
            return text, img
        except:
            return "", None

    def fetch(self):
        results = []
        for url in self.sources:
            feed = feedparser.parse(url)
            for entry in feed.entries[:3]: # Top 3 from each source
                results.append({
                    "id": hashlib.md5(entry.link.encode()).hexdigest(),
                    "title": entry.title,
                    "link": entry.link,
                    "source": url.split('/')[2],
                    "published": entry.get('published', 'N/A')
                })
        return results

# --- STYLING ---
st.markdown("""
    <style>
    .reportview-container { background: #0e1117; }
    .news-card {
        background-color: #161b22;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #238636;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- APP INTERFACE ---
st.title("⚽ Pro Soccer Scout AI: Global Feed")
st.sidebar.header("Scout Controls")
auto_refresh = st.sidebar.checkbox("Auto-Summarize News", value=True)

scraper = SoccerScraper()

if 'news_data' not in st.session_state:
    with st.spinner("Fetching latest pitch reports..."):
        st.session_state.news_data = scraper.fetch()

if st.sidebar.button("🔄 Refresh Feed"):
    st.session_state.news_data = scraper.fetch()
    st.rerun()

# --- DISPLAY FEED ---
for i, item in enumerate(st.session_state.news_data):
    with st.container():
        st.markdown(f"""
            <div class="news-card">
                <small style="color: #8b949e;">{item['source']} | {item['published']}</small>
                <h3 style="margin-top: 0;">{item['title']}</h3>
            </div>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 2])
        
        # Action Button to Analyze
        if col1.button(f"✨ Generate AI Report", key=f"ai_{item['id']}"):
            with st.spinner("AI is reading the article..."):
                raw_text, img_url = scraper.get_content(item['link'])
                
                if img_url:
                    st.image(img_url, use_container_width=True)
                
                if len(raw_text) > 100:
                    summary = summarizer(raw_text[:1024], max_length=60, min_length=30)[0]['summary_text']
                    st.info(f"**AI SUMMARY:** {summary}")
                    
                    # Copyable Text Area
                    st.text_area("Copy for Social Media", 
                                value=f"🚨 UPDATE: {item['title']}\n\n📝 {summary}\n\nSource: {item['link']}", 
                                height=100)
                else:
                    st.warning("Article content too short for AI analysis.")
        
        col2.markdown(f"[Read Full Article]({item['link']})")
        st.divider()
