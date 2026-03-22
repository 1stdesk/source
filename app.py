import streamlit as st
import requests
import feedparser
import hashlib
import time
import random

# --- FUTURISTIC UI CONFIG ---
st.set_page_config(page_title="NEO-SCOUT // AI_READER", page_icon="📡", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background-color: #050505; font-family: 'JetBrains Mono', monospace; }
    h1, h2, h3, p, span, div { color: #00ff41 !important; text-shadow: 0 0 5px #00ff41; }
    .stElementContainer div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #0a0a0a !important;
        border: 1px solid #00ff41 !important;
        padding: 20px; border-radius: 2px; margin-bottom: 20px;
    }
    .intel-label { color: #ff0055 !important; font-weight: bold; font-size: 0.8rem; text-transform: uppercase; }
    .intel-box { background-color: #001a00; border-left: 4px solid #00ff41; padding: 15px; margin: 10px 0; }
    </style>
    """, unsafe_allow_html=True)

# --- NEW AI READER ENGINE ---
def get_clean_markdown(url):
    """Bypasses messy HTML by using an AI Reader to get clean text."""
    try:
        # Prepending r.jina.ai acts as an AI-friendly proxy
        reader_url = f"https://r.jina.ai/{url}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(reader_url, timeout=10, headers=headers)
        if r.status_code == 200:
            return r.text
    except:
        return ""
    return ""

# --- STRUCTURED AI ANALYZER ---
def query_ai_report(text):
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    if "HF_TOKEN" not in st.secrets: return "ERROR: TOKEN_NOT_FOUND"
    
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    # We feed the top of the article for 'What Happened' and 'History'
    payload = {
        "inputs": text[:1200], 
        "parameters": {"do_sample": False, "max_length": 180, "min_length": 90}
    }
    
    for i in range(2):
        try:
            r = requests.post(API_URL, headers=headers, json=payload, timeout=15)
            res = r.json()
            if isinstance(res, list):
                summary = res[0]['summary_text']
                # Smart Splitting Logic for your 3 categories
                sentences = summary.split(". ")
                return {
                    "event": sentences[0] if len(sentences) > 0 else "Analysis pending.",
                    "analysis": sentences[1] if len(sentences) > 1 else "Developing situation.",
                    "history": ". ".join(sentences[2:]) if len(sentences) > 2 else "Historical context in archives."
                }
            time.sleep(3)
        except: continue
    return None

# --- DATA STREAM ---
@st.cache_data(ttl=300)
def get_live_stream():
    sources = [
        "https://www.goal.com/en/feeds/news",
        "https://www.skysports.com/rss/12040",
        "https://feeds.bbci.co.uk/sport/football/rss.xml",
        "https://www.theguardian.com/football/rss"
    ]
    random.shuffle(sources)
    stream = []
    for url in sources[:3]: # Take 3 random sources per refresh
        f = feedparser.parse(url)
        for entry in f.entries[:4]:
            stream.append({
                "id": hashlib.md5(entry.link.encode()).hexdigest(), 
                "title": entry.title.upper(), 
                "link": entry.link, 
                "src": url.split('/')[2].upper()
            })
    return stream

# --- MAIN INTERFACE ---
st.title("📡 NEO-SCOUT // AI_READER_V8.6")

if st.button("🔄 RE-SCAN ALL NODES"):
    st.cache_data.clear()
    st.rerun()

news_stream = get_live_stream()

for item in news_stream:
    with st.container(border=True):
        st.markdown(f"<span class='intel-label'>NODE: {item['src']}</span>", unsafe_allow_html=True)
        st.subheader(item['title'])
        
        if st.button("🔬 GENERATE_DEEP_REPORT", key=item['id']):
            with st.spinner(">> AI IS READING SOURCE CONTENT..."):
                # 1. Get AI-ready text
                clean_text = get_clean_markdown(item['link'])
                
                if len(clean_text) > 200:
                    # 2. Process through BART
                    report = query_ai_report(clean_text)
                    
                    if report:
                        st.markdown(f"""
                            <div class="intel-box">
                                <strong>📍 [THE_EVENT]</strong><br>{report['event']}.<br><br>
                                <strong>🧠 [SYSTEM_ANALYSIS]</strong><br>{report['analysis']}.<br><br>
                                <strong>📜 [HISTORICAL_CONTEXT]</strong><br>{report['history']}
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Ready for Social Media Copy-Paste
                        ready_post = (f"⚽ {item['title']}\n\n"
                                     f"📍 EVENT: {report['event']}\n\n"
                                     f"🧠 ANALYSIS: {report['analysis']}\n\n"
                                     f"📜 HISTORY: {report['history']}\n\n"
                                     f"#Football #ViralNews #NeoScout")
                        
                        st.text_area(">> BROADCAST_READY:", value=ready_post, height=250)
                else:
                    st.error(">> ERROR: SOURCE_ENCRYPTED_OR_BLOCKED")

st.markdown("---")
st.write(">> SYSTEM_ONLINE // AI_READER_ACTIVE")
