import streamlit as st
import feedparser
from newspaper import Article
import torch
from transformers import pipeline
import random

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Pro Soccer Scout v5", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button {
        width: 100%; border-radius: 8px; background-color: #238636; color: white; border: none;
    }
    .stButton>button:hover { background-color: #2ea043; border: none; }
    .scout-card { 
        background-color: #161b22; padding: 20px; border-radius: 12px; 
        border: 1px solid #30363d; margin-bottom: 25px;
    }
    .summary-text {
        background-color: #0d1117; padding: 18px; border-radius: 8px;
        border-left: 5px solid #238636; font-size: 1rem; color: #e6edf3;
        line-height: 1.6; margin-top: 15px;
    }
    .img-container img {
        border-radius: 10px; object-fit: cover; height: 200px; width: 100%;
        border: 1px solid #30363d;
    }
    .source-label { color: #58a6ff; font-weight: bold; font-size: 0.8rem; }
    .headline-text { color: #f0f6fc; font-weight: 800; font-size: 1.6rem; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- AI MODELS ---
@st.cache_resource
def load_summarizer():
    # DistilBART is lighter and faster for Cloud deployments
    return pipeline("summarization", model="sshleifer/distilbart-cnn-12-6", framework="pt")

summarizer = load_summarizer()

# --- UTILITY: DATA FETCHING ---
@st.cache_data(ttl=600)
def fetch_news():
    sources = [
        ("Goal.com", "https://www.goal.com/en/feeds/news"),
        ("Sky Sports", "https://www.skysports.com/rss/12040"),
        ("BBC Sport", "https://push.api.bbci.co.uk/morph/items?page=1&limit=10&feed=football"),
        ("Transfermarkt", "https://www.transfermarkt.com/rss/news")
    ]
    all_news = []
    for name, url in sources:
        try:
            f = feedparser.parse(url)
            for entry in f.entries[:5]:
                all_news.append({'source': name, 'title': entry.title, 'link': entry.link})
        except: continue
    random.shuffle(all_news)
    return all_news

def generate_scout_report(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        
        # 1. Clean Images (Filter out trackers and tiny icons)
        valid_imgs = [i for i in article.images if "ads" not in i and "logo" not in i and "pixel" not in i]
        # Fallback to top_image if list is short
        if article.top_image and article.top_image not in valid_imgs:
            valid_imgs.insert(0, article.top_image)
            
        # 2. AI Summary
        # BART models have a 1024 token limit; we pass roughly the first 3000 chars
        content = article.text[:3000]
        summary = summarizer(content, max_length=150, min_length=45, do_sample=False)[0]['summary_text']
        
        return {"summary": summary, "images": valid_imgs[:3]}
    except Exception as e:
        return None

# --- MAIN APP INTERFACE ---
st.title("⚽ PRO SCOUT: DEEP INTELLIGENCE")
st.subheader("Automated Article Analysis & Visual Scouting")

if 'feed' not in st.session_state:
    st.session_state.feed = fetch_news()

# Search/Filter
search = st.text_input("🔍 Search specific players or clubs...", "")
display_news = [n for n in st.session_state.feed if search.lower() in n['title'].lower()]

# Display Cards
for i, news in enumerate(display_news):
    with st.container():
        st.markdown(f"""
            <div class="scout-card">
                <span class="source-label">{news['source']}</span>
                <div class="headline-text">{news['title']}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Action Trigger
        if st.button(f"⚡ GENERATE FULL SCOUT REPORT", key=f"btn_{i}"):
            with st.spinner("Scraping article & synthesizing intelligence..."):
                report = generate_scout_report(news['link'])
                
                if report:
                    # Summary Section
                    st.markdown(f"""
                        <div class="summary-text">
                            <strong>SCOUT ANALYSIS:</strong><br>{report['summary']}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Image Gallery (3 Pictures)
                    st.markdown("### 📸 Visual Evidence")
                    img_cols = st.columns(3)
                    for idx, img_url in enumerate(report['images']):
                        with img_cols[idx]:
                            st.markdown(f'<div class="img-container">', unsafe_allow_html=True)
                            st.image(img_url, use_container_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.markdown(f"[🔗 Read Original Article]({news['link']})")
                else:
                    st.error("This source is blocking automated scouting. Please try another article.")
        
        st.write("---")

# Refresh logic
if st.sidebar.button("🔄 Refresh Wire"):
    st.cache_data.clear()
    st.rerun()
