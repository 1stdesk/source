import streamlit as st
import requests
import feedparser
import hashlib
from bs4 import BeautifulSoup
import time

# --- FUTURISTIC UI CONFIG ---
st.set_page_config(page_title="NEO-SCOUT v7.0", page_icon="📡", layout="wide")

# Custom CSS for Futuristic/Terminal look
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');

    /* Global Background & Font */
    .stApp {
        background-color: #050505;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Titles and Headers */
    h1, h2, h3, p, span, div {
        color: #00ff41 !important; /* Matrix Green */
        text-shadow: 0 0 5px #00ff41;
    }

    /* Futuristic Cards */
    .stElementContainer div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #0a0a0a !important;
        border: 1px solid #00ff41 !important;
        box-shadow: 0 0 15px rgba(0, 255, 65, 0.2);
        padding: 20px;
        border-radius: 2px;
        margin-bottom: 20px;
    }

    /* Terminal-style Buttons */
    .stButton>button {
        background-color: transparent !important;
        color: #00ff41 !important;
        border: 1px solid #00ff41 !important;
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase;
        letter-spacing: 2px;
        transition: 0.3s;
        border-radius: 0px;
    }

    .stButton>button:hover {
        background-color: #00ff41 !important;
        color: #000 !important;
        box-shadow: 0 0 20px #00ff41;
    }

    /* Deep Intel Box */
    .intel-box {
        background-color: #001a00;
        border-left: 4px solid #00ff41;
        padding: 15px;
        margin: 10px 0;
        font-size: 0.95rem;
        color: #d1ffd1 !important;
        line-height: 1.6;
    }

    /* Input Fields */
    .stTextInput input {
        background-color: #000 !important;
        color: #00ff41 !important;
        border: 1px solid #00ff41 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- AI CORE (Deep Intel Parameters) ---
def query_ai_deep(text):
    API_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-cnn"
    
    if "HF_TOKEN" not in st.secrets:
        return "CRITICAL ERROR: ACCESS_TOKEN_NOT_FOUND"
    
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    payload = {
        "inputs": text[:1500],
        "parameters": {
            "do_sample": False,
            "max_length": 180,
            "min_length": 90,
            "repetition_penalty": 1.3,
            "length_penalty": 1.5
        }
    }

    for i in range(3):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=15)
            result = response.json()
            if isinstance(result, dict) and "estimated_time" in result:
                time.sleep(5)
                continue
            return result[0]['summary_text']
        except:
            continue
    return "SYSTEM_TIMEOUT: MODEL_FAILURE"

# --- DATA STREAM ---
@st.cache_data(ttl=300)
def get_live_stream():
    feeds = [
        "https://www.goal.com/en/feeds/news",
        "https://www.skysports.com/rss/12040",
        "https://www.theguardian.com/football/rss"
    ]
    stream = []
    for url in feeds:
        try:
            f = feedparser.parse(url)
            for entry in f.entries[:6]:
                stream.append({
                    "id": hashlib.md5(entry.link.encode()).hexdigest(),
                    "title": entry.title.upper(),
                    "link": entry.link,
                    "src": url.split('/')[2].upper()
                })
        except: continue
    return stream

def scrape_intel(url):
    try:
        r = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.content, 'html.parser')
        img = soup.find("meta", property="og:image")
        paras = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60]
        return " ".join(paras[:5]), (img["content"] if img else None)
    except: return "", None

# --- MAIN INTERFACE ---
st.title("📡 NEO-SCOUT // INTEL_AGGREGATOR_V7")
st.markdown("---")

# Refresh Control
col_header, col_ref = st.columns([5, 1])
with col_ref:
    if st.button("🔄 REFRESH_LIST"):
        st.cache_data.clear()
        st.rerun()

# Search Buffer
search_buf = st.text_input(">> INITIALIZE_FILTER_QUERY:", "").upper()

# Load Data
news_stream = get_live_stream()
filtered_stream = [n for n in news_stream if search_buf in n['title']] if search_buf else news_stream

# Display Loop
for item in filtered_stream:
    with st.container(border=True):
        st.write(f"SOURCE_NODE: {item['src']}")
        st.subheader(item['title'])
        
        c1, c2 = st.columns([1, 4])
        with c1:
            if st.button("RUN_DEEP_INTEL", key=item['id']):
                with st.spinner(">> DECRYPTING_AND_SUMMARIZING..."):
                    raw_text, image = scrape_intel(item['link'])
                    if image: st.image(image, use_container_width=True)
                    
                    if len(raw_text) > 200:
                        report = query_ai_deep(raw_text)
                        st.markdown(f"""
                            <div class="intel-box">
                                <strong>[AI_SCOUT_DEEP_REPORT]</strong><br><br>
                                {report}
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.write(">> ERROR: DATA_PACKET_TOO_SMALL")
        
        with c2:
            st.markdown(f"[>> ACCESS_FULL_LINK]({item['link']})")

st.markdown("---")
st.write(">> END_OF_STREAM")
