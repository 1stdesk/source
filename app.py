import streamlit as st
import requests
import feedparser
import hashlib
import time
import random

# --- CONFIG & TERMINAL STYLING ---
st.set_page_config(page_title="NEO-SCOUT // V8.7_PRO", page_icon="📡", layout="wide")

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
    .intel-label { color: #ff0055 !important; font-weight: bold; font-size: 0.8rem; text-transform: uppercase; border: 1px solid #ff0055; padding: 2px 4px; }
    .intel-box { background-color: #001a00; border-left: 4px solid #00ff41; padding: 15px; margin: 10px 0; border-radius: 0 5px 5px 0; }
    </style>
    """, unsafe_allow_html=True)

# --- AI READER (Bypasses Paywalls & Cleans HTML) ---
def get_clean_markdown(url):
    """Uses r.jina.ai to strip ads/paywalls and get LLM-ready text."""
    try:
        reader_url = f"https://r.jina.ai/{url}"
        # We add a common User-Agent to look like a standard browser
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        r = requests.get(reader_url, timeout=12, headers=headers)
        if r.status_code == 200 and len(r.text) > 200:
            return r.text
    except:
        return ""
    return ""

# --- STRUCTURED AI ANALYZER (With Wake-Up Logic) ---
def query_ai_report(text):
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    if "HF_TOKEN" not in st.secrets: return None
    
    # CRITICAL: "X-Wait-For-Model" forces the free API to wake up the model
    headers = {
        "Authorization": f"Bearer {st.secrets['HF_TOKEN']}",
        "X-Wait-For-Model": "true",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": text[:1200], # Keep it within token limits for speed
        "parameters": {"do_sample": False, "max_length": 180, "min_length": 80}
    }
    
    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=25)
        res = r.json()
        
        # If the API returns the summary successfully
        if isinstance(res, list) and 'summary_text' in res[0]:
            summary = res[0]['summary_text']
            sentences = [s.strip() for s in summary.split(". ") if len(s) > 10]
            return {
                "event": sentences[0] if len(sentences) > 0 else "Analysis pending.",
                "analysis": sentences[1] if len(sentences) > 1 else "Situation developing.",
                "history": ". ".join(sentences[2:]) if len(sentences) > 2 else "Historical data archived."
            }
    except Exception as e:
        st.error(f">> SATELLITE_LAG: {e}")
    
    # EMERGENCY FALLBACK: If AI is truly down, manually slice the text
    manual_slices = text.split("\n\n")
    clean_slices = [s for s in manual_slices if len(s) > 40]
    return {
        "event": clean_slices[0][:150] if len(clean_slices) > 0 else "Intel stream offline.",
        "analysis": "MANUAL_RECOVERY: Signal interference detected.",
        "history": "HISTORICAL_ARCHIVES: Check source link for deep context."
    }

# --- PAYWALL-FREE SOURCE FEED ---
@st.cache_data(ttl=600)
def get_live_stream():
    # Audited for 2026 (No Hard Paywalls)
    sources = [
        "https://feeds.bbci.co.uk/sport/football/rss.xml",
        "https://www.skysports.com/rss/12040",
        "https://www.goal.com/en/feeds/news",
        "https://www.espn.com/espn/rss/soccer/news",
        "https://www.90min.com/posts.rss",
        "https://www.football365.com/feed"
    ]
    random.shuffle(sources)
    stream = []
    for url in sources[:4]: # Sample 4 random nodes
        try:
            f = feedparser.parse(url)
            src_label = url.split('/')[2].upper().replace('WWW.', '')
            for entry in f.entries[:4]:
                stream.append({
                    "id": hashlib.md5(entry.link.encode()).hexdigest(), 
                    "title": entry.title.upper(), 
                    "link": entry.link, 
                    "src": src_label
                })
        except: continue
    return stream

# --- MAIN UI ---
st.title("📡 NEO-SCOUT // V8.7_BATTLE_HARDENED")

if st.button("🔄 RE-SCAN GLOBAL NODES"):
    st.cache_data.clear()
    st.rerun()

news_stream = get_live_stream()

for item in news_stream:
    with st.container(border=True):
        st.markdown(f"<span class='intel-label'>NODE: {item['src']}</span>", unsafe_allow_html=True)
        st.subheader(item['title'])
        
        if st.button("🔬 DECRYPT_DEEP_REPORT", key=item['id']):
            with st.spinner(">> INTERCEPTING_PACKETS..."):
                # 1. Clean the website content (bypass paywalls)
                content = get_clean_markdown(item['link'])
                
                if content:
                    # 2. Structured AI Processing
                    report = query_ai_report(content)
                    
                    if report:
                        st.markdown(f"""
                            <div class="intel-box">
                                <strong>📍 [THE_EVENT]</strong><br>{report['event']}.<br><br>
                                <strong>🧠 [SYSTEM_ANALYSIS]</strong><br>{report['analysis']}.<br><br>
                                <strong>📜 [HISTORICAL_CONTEXT]</strong><br>{report['history']}
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Ready for Social Media
                        ready_post = (f"⚽ {item['title']}\n\n"
                                     f"📍 EVENT: {report['event']}\n\n"
                                     f"🧠 ANALYSIS: {report['analysis']}\n\n"
                                     f"📜 HISTORY: {report['history']}\n\n"
                                     f"#FootballNews #NeoScout #ViralReport")
                        
                        st.text_area(">> READY_TO_BROADCAST:", value=ready_post, height=250)
                else:
                    st.error(">> ACCESS_DENIED: NODE_PROTECTED_OR_OFFLINE")

st.markdown("---")
st.write(">> SYSTEM_ACTIVE // ALL_NODES_STABLE")
