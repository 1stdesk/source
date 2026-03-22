import streamlit as st
import requests
import feedparser
import hashlib
from bs4 import BeautifulSoup
import time
import random

# --- CONFIG ---
st.set_page_config(page_title="NEO-SCOUT // V8.5_PRO", page_icon="📡", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background-color: #050505; font-family: 'JetBrains Mono', monospace; }
    .report-header { color: #00ff41; font-weight: bold; border-bottom: 1px solid #333; margin-top: 15px; text-transform: uppercase; letter-spacing: 1px; }
    .report-content { color: #d1ffd1; margin-bottom: 10px; font-size: 0.95rem; line-height: 1.5; padding: 5px 0; }
    </style>
    """, unsafe_allow_html=True)

# --- ROBUST AI PROCESSING ---
def query_ai_scout(text, task_type="summary"):
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    if "HF_TOKEN" not in st.secrets: return "TOKEN_MISSING"
    
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    payload = {"inputs": text[:1024], "parameters": {"max_length": 100, "min_length": 40}}
    
    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=10)
        res = r.json()
        if isinstance(res, list) and 'summary_text' in res[0]:
            return res[0]['summary_text'].strip()
    except:
        pass
    
    # EMERGENCY FALLBACK: If AI fails, return the cleaned raw segment
    return text[:150] + "..."

# --- DEEP SCRAPER V2 ---
def scrape_intel_pro(url):
    try:
        r = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # 1. Image Extraction
        img = soup.find("meta", property="og:image")
        img_url = img["content"] if img else None

        # 2. Description Fallback (Important for blocked sites)
        meta_desc = soup.find("meta", property="og:description")
        desc_text = meta_desc["content"] if meta_desc else ""

        # 3. Paragraph Extraction
        paras = [" ".join(p.get_text().split()) for p in soup.find_all('p') if len(p.get_text()) > 50]
        
        # 4. Data Validation: If paragraphs fail, use meta description
        if len(paras) < 2 and len(desc_text) > 20:
            # Split the description into chunks to simulate different sections
            paras = [desc_text, desc_text, desc_text]
            
        return paras, img_url
    except:
        return [], None

# --- FEED GENERATOR ---
@st.cache_data(ttl=300)
def get_randomized_feed():
    # Adding more diverse endpoints
    sources = [
        "https://www.goal.com/en/feeds/news", 
        "https://www.skysports.com/rss/12040", 
        "https://feeds.bbci.co.uk/sport/football/rss.xml",
        "https://www.espn.com/espn/rss/soccer/news"
    ]
    random.shuffle(sources)
    stream = []
    for url in sources[:3]:
        f = feedparser.parse(url)
        for entry in f.entries[:5]:
            stream.append({
                "id": hashlib.md5(entry.link.encode()).hexdigest(), 
                "title": entry.title.upper(), 
                "link": entry.link, 
                "src": url.split('/')[2]
            })
    return stream

# --- MAIN UI ---
st.title("📡 NEO-SCOUT // INTEL_REPORT_V8.5")

if st.button("🔄 RE-SCAN NODES"):
    st.cache_data.clear()
    st.rerun()

for item in get_randomized_feed():
    with st.container(border=True):
        st.write(f"NODE: {item['src'].upper()}")
        st.subheader(item['title'])
        
        if st.button("🔬 RUN_INTEL_SCAN", key=item['id']):
            with st.spinner(">> INTERCEPTING_ENCRYPTED_PACKETS..."):
                paras, image = scrape_intel_pro(item['link'])
                
                if paras:
                    if image: st.image(image, use_container_width=True)
                    
                    # Logic: Distribute the available text across the 3 categories
                    event_txt = paras[0]
                    analysis_txt = paras[min(1, len(paras)-1)]
                    history_txt = paras[-1] if len(paras) > 2 else "No further historical data found in this transmission."

                    # AI Calls
                    event = query_ai_scout(event_txt, "summary")
                    analysis = query_ai_scout(analysis_txt, "analysis")
                    history = query_ai_scout(history_txt, "history")

                    # DISPLAY UI
                    st.markdown(f'<div class="report-header">📍 [THE_EVENT]</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="report-content">{event}</div>', unsafe_allow_html=True)
                    
                    st.markdown(f'<div class="report-header">🧠 [SYSTEM_ANALYSIS]</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="report-content">Analysis suggests: {analysis}</div>', unsafe_allow_html=True)
                    
                    st.markdown(f'<div class="report-header">📜 [HISTORICAL_CONTEXT]</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="report-content">{history}</div>', unsafe_allow_html=True)

                    # BROADCAST FORMAT
                    ready_post = (f"⚽ {item['title']}\n\n"
                                 f"📍 EVENT: {event}\n\n"
                                 f"🧠 ANALYSIS: {analysis}\n\n"
                                 f"📜 HISTORY: {history}\n\n"
                                 f"🔗 Source: {item['link']}\n\n"
                                 f"#FootballNews #ViralIntel #ScoutReport")
                    
                    st.text_area(">> READY_TO_BROADCAST:", value=ready_post, height=300)
                else:
                    st.error(">> ERROR: NODE_TIMEOUT // SOURCE_PROTECTED")

st.markdown("---")
st.write(">> SYSTEM_STABLE // END_OF_LINE")
