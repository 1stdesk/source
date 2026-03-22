import streamlit as st
import requests
import feedparser
import hashlib
from bs4 import BeautifulSoup
import time

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Pro Soccer Scout AI v6.0", 
    page_icon="⚽", 
    layout="wide"
)

# --- STYLING ---
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { 
        width: 100%; border-radius: 8px; height: 3em; 
        background-color: #238636; color: white; font-weight: bold;
        border: none; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #2ea043; border: 1px solid white; }
    .report-box { 
        background-color: #161b22; padding: 20px; 
        border-radius: 10px; border: 1px solid #30363d;
        line-height: 1.6; color: #e6edf3;
    }
    .source-tag { color: #58a6ff; font-size: 0.8rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- AI API LOGIC (The "Self-Healing" Engine) ---
def query_ai(text):
    """Sends text to Hugging Face API with automatic retry for 'Cold Starts'."""
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    
    if "HF_TOKEN" not in st.secrets:
        st.error("Missing 'HF_TOKEN' in Streamlit Secrets!")
        return None
    
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    payload = {
        "inputs": text[:1024],
        "parameters": {"do_sample": False, "max_length": 100, "min_length": 40}
    }

    # Attempt to call the API up to 3 times if it's warming up
    for i in range(3):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=20)
            result = response.json()

            # Handle Model Loading/Warming up
            if isinstance(result, dict) and "estimated_time" in result:
                wait_time = int(result['estimated_time'])
                st.info(f"⏳ AI is warming up (Attempt {i+1}/3). Waiting {min(wait_time, 10)}s...")
                time.sleep(min(wait_time, 10))
                continue
            
            # Handle Success
            if isinstance(result, list) and len(result) > 0:
                return result[0]['summary_text']
            
            return f"⚠️ API Error: {result}"
        
        except Exception as e:
            if i == 2: return f"❌ Connection Timeout: {e}"
            time.sleep(2)
            
    return "😴 The AI is taking too long to wake up. Please try again in 30 seconds."

# --- SCRAPER LOGIC ---
@st.cache_data(ttl=600) # Cache news for 10 minutes
def fetch_soccer_news():
    feeds = [
        "https://www.goal.com/en/feeds/news",
        "https://www.skysports.com/rss/12040",
        "https://www.theguardian.com/football/rss"
    ]
    all_articles = []
    for url in feeds:
        try:
            f = feedparser.parse(url)
            for entry in f.entries[:5]:
                all_articles.append({
                    "id": hashlib.md5(entry.link.encode()).hexdigest(),
                    "title": entry.title,
                    "link": entry.link,
                    "source": url.split('/')[2],
                    "published": entry.get('published', 'Recently')
                })
        except: continue
    return all_articles

def get_full_article_data(url):
    try:
        r = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Extract image
        img_tag = soup.find("meta", property="og:image")
        img = img_tag["content"] if img_tag else None
        
        # Extract first 3 solid paragraphs for AI
        paras = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60]
        text = " ".join(paras[:3])
        return text, img
    except:
        return "", None

# --- UI LAYOUT ---
st.title("⚽ Pro Soccer Scout AI")
st.markdown("### Global Intelligence Aggregator")

# Sidebar
with st.sidebar:
    st.header("Scout Controls")
    if st.button("🔄 Refresh Global Feed"):
        st.cache_data.clear()
        st.rerun()
    st.divider()
    st.write("Using **Facebook BART-Large-CNN** for tactical summaries.")

# Initialize News
news_feed = fetch_soccer_news()

# Display News Cards
for article in news_feed:
    with st.container():
        st.markdown(f"<span class='source-tag'>{article['source'].upper()}</span>", unsafe_allow_html=True)
        st.subheader(article['title'])
        
        col_act, col_link = st.columns([1, 4])
        
        # Action: Summarize
        if col_act.button("✨ Analyze Story", key=article['id']):
            with st.spinner("Scouting article content..."):
                full_text, image_url = get_article_data = get_full_article_data(article['link'])
                
                if image_url:
                    st.image(image_url, use_container_width=True)
                
                if len(full_text) > 100:
                    summary = query_ai(full_text)
                    if summary:
                        st.markdown(f"""
                            <div class='report-box'>
                                <strong>AI SCOUT SUMMARY:</strong><br>{summary}
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Copy-Paste Section
                        st.text_area("Shareable Text", 
                                    value=f"🚨 FOOTBALL UPDATE: {article['title']}\n\n📝 AI SUMMARY: {summary}\n\n🔗 Full Story: {article['link']}",
                                    height=100)
                else:
                    st.warning("Could not retrieve enough content from this source to summarize.")
        
        col_link.markdown(f"<br>[Read Original Article]({article['link']})", unsafe_allow_html=True)
        st.divider()
