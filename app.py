import streamlit as st
import requests
import feedparser
import hashlib
from bs4 import BeautifulSoup
import time

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Pro Soccer Scout AI", 
    page_icon="⚽", 
    layout="wide"
)

# --- STYLING ---
st.markdown("""
    <style>
    .main { background-color: #0d1117; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #238636; color: white; }
    .report-box { background-color: #161b22; padding: 20px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- AI API LOGIC ---
def query_ai(text):
    """Sends text to Hugging Face Inference API for summarization."""
    # Using the BART model via API to save local memory
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    
    # Check if Secret is set
    if "HF_TOKEN" not in st.secrets:
        return "❌ Error: HF_TOKEN not found in Streamlit Secrets."
    
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    payload = {
        "inputs": text[:1024], # API limit is usually 1024 tokens
        "parameters": {"do_sample": False, "max_length": 80, "min_length": 30}
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        result = response.json()
        
        # Handle API 'Warming Up' state
        if isinstance(result, dict) and "estimated_time" in result:
            wait_time = int(result['estimated_time'])
            return f"⏳ AI is warming up on the server. Please wait {wait_time}s and click 'Analyze' again."
        
        return result[0]['summary_text']
    except Exception as e:
        return f"⚠️ AI Connection Error: {str(e)}"

# --- SCRAPER FUNCTIONS ---
def fetch_news():
    """Fetches latest soccer news from top RSS feeds."""
    feeds = [
        "https://www.goal.com/en/feeds/news",
        "https://www.skysports.com/rss/12040",
        "https://www.theguardian.com/football/rss"
    ]
    articles = []
    for url in feeds:
        try:
            f = feedparser.parse(url)
            for entry in f.entries[:5]:
                articles.append({
                    "id": hashlib.md5(entry.link.encode()).hexdigest(),
                    "title": entry.title,
                    "link": entry.link,
                    "source": url.split('/')[2],
                    "date": entry.get('published', 'Recently')
                })
        except:
            continue
    return articles

def get_article_data(url):
    """Scrapes the main image and body text from the article link."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, timeout=5, headers=headers)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Find high-res image
        img_tag = soup.find("meta", property="og:image")
        img = img_tag["content"] if img_tag else None
        
        # Get first 3 paragraphs for the AI to read
        paras = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 50]
        text = " ".join(paras[:3])
        
        return text, img
    except:
        return "", None

# --- MAIN UI ---
st.title("⚽ Global Soccer Scout AI")
st.subheader("Near Real-Time Intelligence & AI Summaries")

# Sidebar
with st.sidebar:
    st.header("Scout Settings")
    if st.button("🔄 Refresh News Feed"):
        st.session_state.feed = fetch_news()
        st.rerun()
    st.info("AI summaries are generated using the Facebook BART model via Hugging Face API.")

# Initialize Feed
if 'feed' not in st.session_state:
    with st.spinner("Initial news sweep..."):
        st.session_state.feed = fetch_news()

# Display Articles
for item in st.session_state.feed:
    with st.container():
        # Clean UI Card
        st.markdown(f"### {item['title']}")
        st.caption(f"📍 {item['source'].upper()} | 🕒 {item['date']}")
        
        col1, col2 = st.columns([1, 4])
        
        with col1:
            if st.button("🔍 Analyze Story", key=item['id']):
                with st.spinner("AI is reading..."):
                    raw_text, img_url = get_article_data(item['link'])
                    
                    if img_url:
                        st.image(img_url, use_container_width=True)
                    
                    if len(raw_text) > 100:
                        summary = query_ai(raw_text)
                        st.markdown(f"""
                            <div class="report-box">
                                <strong>AI SCOUT REPORT:</strong><br>{summary}
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Copy/Paste Helper
                        st.text_area("Copy Report", 
                                    value=f"🚨 UPDATE: {item['title']}\n\n📝 {summary}\n\n🔗 {item['link']}", 
                                    height=100)
                    else:
                        st.warning("Article body is too short or blocked for AI analysis.")
        
        with col2:
            st.markdown(f"[View Original Article]({item['link']})")
        
        st.divider()
