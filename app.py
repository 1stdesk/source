import streamlit as st
import requests
import feedparser
import hashlib
from bs4 import BeautifulSoup
import time
import random

# --- CONFIG ---
st.set_page_config(page_title="NEO-SCOUT // INTEL_V8.4", page_icon="📡", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background-color: #050505; font-family: 'JetBrains Mono', monospace; }
    .report-header { color: #00ff41; font-weight: bold; border-bottom: 1px solid #00ff41; margin-top: 15px; }
    .report-content { color: #d1ffd1; margin-bottom: 10px; font-size: 0.9rem; line-height: 1.4; }
    .stElementContainer div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #0a0a0a !important;
        border: 1px solid #00ff41 !important;
        padding: 20px; border-radius: 2px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- AI CORE (Multi-Stage Processing) ---
def query_ai_scout(text, task_type="summary"):
    """Customized AI calls based on the report section."""
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    if "HF_TOKEN" not in st.secrets: return "ERROR: TOKEN_REQUIRED"
    
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    
    # Adjust parameters based on what we want the AI to focus on
    params = {
        "summary": {"max_length": 100, "min_length": 40, "repetition_penalty": 1.0},
        "analysis": {"max_length": 120, "min_length": 50, "repetition_penalty": 1.5},
        "history": {"max_length": 80, "min_length": 30, "repetition_penalty": 1.2}
    }
    
    payload = {"inputs": text[:1024], "parameters": params.get(task_type, params["summary"])}
    
    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=15)
        res = r.json()
        if isinstance(res, list): 
            return res[0]['summary_text'].replace(" .", ".").strip()
    except:
        pass
    
    return "Insufficient data for this sector."

# --- DATA EXTRACTION ---
def scrape_intel(url):
    try:
        r = requests.get(url, timeout=7, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.content, 'html.parser')
        img = soup.find("meta", property="og:image")
        paras = [" ".join(p.get_text().split()) for p in soup.find_all('p') if len(p.get_text()) > 60]
        # Filter junk
        clean_paras = [p for p in paras if not any(x in p.lower() for x in ["attendance:", "vs", "referee:"])]
        return clean_paras, (img["content"] if img else None)
    except: return [], None

@st.cache_data(ttl=300)
def get_randomized_feed():
    sources = ["https://www.goal.com/en/feeds/news", "https://www.skysports.com/rss/12040", "https://feeds.bbci.co.uk/sport/football/rss.xml"]
    random.shuffle(sources)
    stream = []
    for url in sources[:3]:
        f = feedparser.parse(url)
        for entry in f.entries[:4]:
            stream.append({"id": hashlib.md5(entry.link.encode()).hexdigest(), "title": entry.title.upper(), "link": entry.link, "src": url.split('/')[2]})
    return stream

# --- UI MAIN ---
st.title("📡 NEO-SCOUT // DEEP_INTEL_REPORT")

if st.button("🔄 RE-SCAN SATELLITE"):
    st.cache_data.clear()
    st.rerun()

for item in get_randomized_feed():
    with st.container(border=True):
        st.write(f"NODE: {item['src'].upper()}")
        st.subheader(item['title'])
        
        if st.button("🔬 RUN_DEEP_ANALYSIS", key=item['id']):
            with st.spinner(">> INTERCEPTING_DATA..."):
                paras, image = scrape_intel(item['link'])
                
                if len(paras) >= 3:
                    if image: st.image(image, use_container_width=True)
                    
                    # Section 1: What Happened (Summary of lead paragraphs)
                    what_happened = query_ai_scout(paras[0] + " " + paras[1], "summary")
                    
                    # Section 2: System Analysis (Summary of middle paragraphs)
                    analysis = query_ai_scout(paras[min(2, len(paras)-1)], "analysis")
                    
                    # Section 3: Historical Context (Summary of later paragraphs often contain history/stats)
                    history = query_ai_scout(paras[-1], "history")

                    # DISPLAY THE STRUCTURED REPORT
                    st.markdown(f"""
                    <div class="report-header">📍 [THE_EVENT]</div>
                    <div class="report-content">{what_happened}</div>
                    
                    <div class="report-header">🧠 [SYSTEM_ANALYSIS]</div>
                    <div class="report-content">The situation suggests {analysis}</div>
                    
                    <div class="report-header">📜 [HISTORICAL_CONTEXT]</div>
                    <div class="report-content">{history}</div>
                    """, unsafe_allow_html=True)
                    
                    # READY TO POST
                    ready_post = (f"🚨 {item['title']}\n\n"
                                 f"📍 WHAT HAPPENED: {what_happened}\n\n"
                                 f"🧠 ANALYSIS: {analysis}\n\n"
                                 f"📜 HISTORY: {history}\n\n"
                                 f"#Football #BreakingNews #Viral")
                    
                    st.text_area(">> BROADCAST_READY_FORMAT:", value=ready_post, height=300)
                else:
                    st.error(">> ERROR: INSUFFICIENT_DATA_NODES")

st.markdown("---")
st.write(">> END_OF_LINE")
