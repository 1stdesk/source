import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import hashlib
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="Soccer Scout AI v3.1", page_icon="⚽", layout="wide")

# --- AI SETUP (Self-Healing) ---
@st.cache_resource
def load_summarizer():
    try:
        # We specify the model directly and let the pipeline infer the task
        # This bypasses the KeyError: 'summarization'
        pipe = pipeline(
            model="sshleifer/distilbart-cnn-12-6", 
            device=-1  # Force CPU for Streamlit Cloud
        )
        return pipe
    except Exception as e:
        st.error(f"AI Loading Error: {e}")
        return None

# Global access to the model
summarizer = load_summarizer()

# --- UTILS ---
class SoccerScraper:
    def fetch_rss(self):
        # Default reliable sources
        feeds = [
            "https://www.goal.com/en/feeds/news",
            "https://www.skysports.com/rss/12040",
            "https://www.theguardian.com/football/rss"
        ]
        results = []
        for url in feeds:
            try:
                f = feedparser.parse(url)
                for entry in f.entries[:5]:
                    results.append({
                        "id": hashlib.md5(entry.link.encode()).hexdigest(),
                        "title": entry.title,
                        "link": entry.link,
                        "source": url.split('/')[2]
                    })
            except: continue
        return results

    def get_full_text(self, url):
        try:
            r = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(r.content, 'html.parser')
            img = soup.find("meta", property="og:image")
            paras = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60]
            return " ".join(paras[:3]), (img["content"] if img else None)
        except:
            return "", None

# --- UI ---
st.title("⚽ Pro Soccer Scout AI")

# Sidebar Debug
with st.sidebar:
    st.header("System Status")
    if summarizer:
        st.success("✅ AI Engine Online")
    else:
        st.error("❌ AI Engine Offline")
    
    if st.button("Clear Cache & Reload"):
        st.cache_resource.clear()
        st.rerun()

scraper = SoccerScraper()

if 'news' not in st.session_state:
    st.session_state.news = scraper.fetch_rss()

# Display News
for item in st.session_state.news:
    with st.expander(f"{item['source'].upper()} | {item['title']}"):
        col1, col2 = st.columns([1, 2])
        
        if col1.button("Analyze with AI", key=f"btn_{item['id']}"):
            if not summarizer:
                st.warning("AI model not loaded. Check logs.")
            else:
                with st.spinner("Scouting article content..."):
                    text, img = scraper.get_full_text(item['link'])
                    if img: st.image(img)
                    
                    if len(text) > 100:
                        # Use generic __call__ to ensure compatibility
                        summary = summarizer(text[:1024], max_length=50, min_length=20)[0]
                        # Support both old and new output formats
                        sum_text = summary.get('summary_text') or summary.get('generated_text')
                        st.info(f"**AI Summary:** {sum_text}")
                    else:
                        st.write("Content too short to summarize.")
        
        col2.markdown(f"[Read Source Article]({item['link']})")
