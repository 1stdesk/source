import streamlit as st
import requests
import feedparser
import hashlib
from bs4 import BeautifulSoup
import time

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Soccer Scout AI v6.1", 
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
        border: none;
    }
    .report-box { 
        background-color: #161b22; padding: 20px; 
        border-radius: 10px; border: 1px solid #30363d;
        line-height: 1.6; color: #e6edf3;
    }
    </style>
    """, unsafe_allow_html=True)

# --- AI API LOGIC (The New 2026 Router Fix) ---
def query_ai(text):
    """Sends text to the NEW Hugging Face Router API."""
    # UPDATED ENDPOINT FOR 2026
    API_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-cnn"
    
    if "HF_TOKEN" not in st.secrets:
        st.error("Error: 'HF_TOKEN' not found in Streamlit Secrets.")
        return None
    
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    payload = {
        "inputs": text[:1024],
        "parameters": {"do_sample": False, "max_length": 90, "min_length": 35}
    }

    # Handle 'Cold Start' (Model Loading)
    for i in range(3):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=15)
            result = response.json()

            if isinstance(result, dict) and "estimated_time" in result:
                st.info(f"⏳ AI is warming up... waiting {int(result['estimated_time'])}s")
                time.sleep(8)
                continue
            
            if isinstance(result, list) and len(result) > 0:
                return result[0]['summary_text']
            
            return f"⚠️ API Error: {result}"
        except Exception as e:
            if i == 2: return f"❌ Connection Timeout: {e}"
            time.sleep(2)
    return "😴 AI timed out. Please try again."

# --- DATA FUNCTIONS ---
@st.cache_data(ttl=600)
def fetch_news():
    feeds = [
        "https://www.goal.com/en/feeds/news",
        "https://www.skysports.com/rss/12040",
        "https://www.theguardian.com/football/rss"
    ]
    data = []
    for url in feeds:
        try:
            f = feedparser.parse(url)
            for entry in f.entries[:8]:
                data.append({
                    "id": hashlib.md5(entry.link.encode()).hexdigest(),
                    "title": entry.title,
                    "link": entry.link,
                    "source": url.split('/')[2]
                })
        except: continue
    return data

def get_content(url):
    try:
        r = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.content, 'html.parser')
        img = soup.find("meta", property="og:image")
        paras = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60]
        return " ".join(paras[:3]), (img["content"] if img else None)
    except: return "", None

# --- UI MAIN ---
st.title("⚽ Pro Soccer Scout AI")

# Search Bar Fix
search_query = st.text_input("🔍 Search for a team, player, or league (e.g. 'Arsenal' or 'La Liga')", "")

# Refresh Button
if st.sidebar.button("🔄 Refresh Feed"):
    st.cache_data.clear()
    st.rerun()

all_news = fetch_news()

# Filter News based on search
filtered_news = [n for n in all_news if search_query.lower() in n['title'].lower()] if search_query else all_news

if not filtered_news:
    st.warning("No news found for that search. Try something else!")

for item in filtered_news:
    with st.container(border=True):
        st.markdown(f"**{item['source'].upper()}**")
        st.subheader(item['title'])
        
        if st.button("✨ Analyze Story", key=item['id']):
            with st.spinner("Analyzing..."):
                text, img = get_content(item['link'])
                if img: st.image(img, use_container_width=True)
                
                if len(text) > 100:
                    report = query_ai(text)
                    st.markdown(f"<div class='report-box'><strong>AI SUMMARY:</strong><br>{report}</div>", unsafe_allow_html=True)
                else:
                    st.warning("Article too short to summarize.")
        
        st.caption(f"[Read full story]({item['link']})")
