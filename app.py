import streamlit as st
import requests
import feedparser
import hashlib
from bs4 import BeautifulSoup
import time

# --- CONFIG ---
st.set_page_config(page_title="Soccer Scout AI v6.2", page_icon="⚽", layout="wide")

# --- STYLING ---
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stButton>button { 
        width: 100%; border-radius: 8px; height: 3.5em; 
        background-color: #238636; color: white; font-weight: bold;
        border: none; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #2ea043; border: 1px solid white; }
    .report-box { 
        background-color: #161b22; padding: 25px; 
        border-radius: 12px; border: 1px solid #30363d;
        line-height: 1.7; color: #e6edf3; font-size: 1.05rem;
    }
    </style>
    """, unsafe_allow_html=True)

# --- DEEP AI LOGIC (BART-LARGE-CNN) ---
def query_ai_deep(text):
    """Sends text to the New Router API with 'Deep' parameter tuning."""
    API_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-cnn"
    
    if "HF_TOKEN" not in st.secrets:
        st.error("Missing HF_TOKEN in Secrets!")
        return None
    
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    
    # DEEP SETTINGS: 
    # repetition_penalty prevents looping. 
    # length_penalty 2.0 encourages more detail.
    payload = {
        "inputs": text[:1500], 
        "parameters": {
            "do_sample": False,
            "max_length": 180,  # Keeps it well under 200 words
            "min_length": 80,   # Ensures it's not too short/shallow
            "repetition_penalty": 1.2,
            "length_penalty": 2.0 
        }
    }

    for i in range(3):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=20)
            result = response.json()

            if isinstance(result, dict) and "estimated_time" in result:
                st.info(f"⏳ AI is analyzing deeply... (Wait {int(result['estimated_time'])}s)")
                time.sleep(8)
                continue
            
            if isinstance(result, list) and len(result) > 0:
                return result[0]['summary_text']
            
            return f"⚠️ API Error: {result}"
        except Exception as e:
            if i == 2: return f"❌ Timeout: {e}"
            time.sleep(2)
    return "😴 AI is resting. Try again in 10s."

# --- DATA FUNCTIONS ---
def get_soccer_news():
    feeds = ["https://www.goal.com/en/feeds/news", "https://www.skysports.com/rss/12040", "https://www.theguardian.com/football/rss"]
    articles = []
    for url in feeds:
        try:
            f = feedparser.parse(url)
            for entry in f.entries[:5]:
                articles.append({
                    "id": hashlib.md5(entry.link.encode()).hexdigest(),
                    "title": entry.title,
                    "link": entry.link,
                    "source": url.split('/')[2]
                })
        except: continue
    return articles

def fetch_article_body(url):
    try:
        r = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.content, 'html.parser')
        img = soup.find("meta", property="og:image")
        # Grab more paragraphs for a "Deeper" context
        paras = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 70]
        return " ".join(paras[:5]), (img["content"] if img else None)
    except: return "", None

# --- UI ---
st.title("⚽ Pro Scout AI: Deep Intel")

if 'news_data' not in st.session_state:
    st.session_state.news_data = get_soccer_news()

# Search Feature
query = st.text_input("🔍 Search Teams or Players", "").lower()

for item in st.session_state.news_data:
    if query and query not in item['title'].lower():
        continue
        
    with st.container(border=True):
        st.caption(item['source'].upper())
        st.subheader(item['title'])
        
        if st.button("🔬 RUN DEEP ANALYSIS", key=item['id']):
            with st.spinner("AI performing deep tactical summary..."):
                text, img = fetch_article_body(item['link'])
                if img: st.image(img, use_container_width=True)
                
                if len(text) > 200:
                    summary = query_ai_deep(text)
                    st.markdown(f"""
                        <div class="report-box">
                            <strong>TACTICAL REPORT:</strong><br><br>{summary}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Social Share Copy
                    st.text_area("Share this Report", f"⚽ {item['title']}\n\n{summary}\n\nFull story: {item['link']}", height=120)
                else:
                    st.error("Insufficient source data for a deep summary.")
        
        st.markdown(f"[Source Article]({item['link']})")
