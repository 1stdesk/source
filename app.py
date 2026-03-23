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
        width: 100%; border-radius: 8px; background-color: #238636; color: white; 
        border: none; font-weight: bold; height: 45px;
    }
    .stButton>button:hover { background-color: #2ea043; border: none; }
    .scout-card { 
        background-color: #161b22; padding: 20px; border-radius: 12px; 
        border: 1px solid #30363d; margin-bottom: 20px;
    }
    .summary-text {
        background-color: #0d1117; padding: 20px; border-radius: 8px;
        border-left: 5px solid #238636; font-size: 1.05rem; color: #e6edf3;
        line-height: 1.6; margin: 20px 0;
    }
    .source-label { color: #58a6ff; font-weight: bold; font-size: 0.8rem; text-transform: uppercase; }
    .headline-text { color: #f0f6fc; font-weight: 800; font-size: 1.7rem; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- AI MODELS (Summarization Only) ---
@st.cache_resource
def load_summarizer():
    # Switching to DistilBART for faster, more stable cloud deployment
    return pipeline("summarization", model="sshleifer/distilbart-cnn-12-6", framework="pt")

summarizer = load_summarizer()

# --- UTILITY FUNCTIONS ---
@st.cache_data(ttl=600)
def fetch_news():
    sources = [
        ("Goal.com", "https://www.goal.com/en/feeds/news"),
        ("Sky Sports", "https://www.skysports.com/rss/12040"),
        ("BBC Sport", "https://push.api.bbci.co.uk/morph/items?page=1&limit=10&feed=football"),
        ("Transfermarkt", "https://www.transfermarkt.com/rss/news"),
        ("90min", "https://www.90min.com/posts.rss")
    ]
    results = []
    for name, url in sources:
        try:
            f = feedparser.parse(url)
            for entry in f.entries[:5]:
                results.append({'s': name, 't': entry.title, 'l': entry.link})
        except: continue
    random.shuffle(results)
    return results

def get_scout_intel(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        
        # AI Summary (Safety: slice text to 3000 chars to avoid model overflow)
        text_to_summarize = article.text[:3000]
        summary_result = summarizer(text_to_summarize, max_length=150, min_length=45, do_sample=False)
        summary = summary_result[0]['summary_text']
        
        # Image Extraction: Filter out small UI elements
        imgs = [i for i in article.images if "logo" not in i.lower() and "icon" not in i.lower()]
        
        # Ensure we have the main article image if available
        if article.top_image and article.top_image not in imgs:
            imgs.insert(0, article.top_image)
            
        return {"summary": summary, "images": imgs[:3]}
    except Exception as e:
        return None

# --- MAIN UI ---
st.title("⚽ PRO SCOUT: DEEP INTELLIGENCE")
st.caption("Real-time football news analysis with AI summarization and visual scouting.")

if 'news_feed' not in st.session_state:
    st.session_state.news_feed = fetch_news()

# Search Bar
search = st.text_input("🔍 Filter News Wire...", "")
display_list = [n for n in st.session_state.news_feed if search.lower() in n['t'].lower()]

# News Feed
for i, news in enumerate(display_list):
    with st.container():
        st.markdown(f"""
            <div class="scout-card">
                <span class="source-label">{news['s']}</span>
                <div class="headline-text">{news['t']}</div>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button(f"⚡ RUN DEEP SCOUT REPORT", key=f"btn_{i}"):
            with st.spinner("Analyzing article data and fetching visuals..."):
                intel = get_scout_intel(news['l'])
                
                if intel:
                    # AI Summary Block
                    st.markdown(f"""
                        <div class="summary-text">
                            <b>AI ANALYSIS:</b><br>{intel['summary']}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # 3-Image Gallery
                    st.markdown("### 📸 Visual Evidence")
                    cols = st.columns(3)
                    for idx, img_url in enumerate(intel['images']):
                        with cols[idx]:
                            st.image(img_url, use_container_width=True)
                    
                    st.markdown(f"🔗 [Read Full Article]({news['l']})")
                else:
                    st.error("Scout error: Could not bypass security or extract data from this source.")
        st.write("---")

# Sidebar Refresh
if st.sidebar.button("🔄 Refresh Market Wire"):
    st.cache_data.clear()
    st.rerun()
    
