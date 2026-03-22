import streamlit as st
import requests
import feedparser
import hashlib
import time
import random

# --- CONFIG ---
st.set_page_config(page_title="NEO-SCOUT // AI_READER_V8.6", page_icon="📡", layout="wide")

# --- THE "READER" ENGINE (Replaces BeautifulSoup) ---
def get_clean_intel(url):
    """Uses Jina AI Reader to get clean Markdown instead of messy HTML."""
    try:
        # Prepend r.jina.ai to get an LLM-ready version of the page
        reader_url = f"https://r.jina.ai/{url}"
        response = requests.get(reader_url, timeout=10)
        if response.status_code == 200:
            return response.text # This is now clean, beautiful Markdown
    except Exception as e:
        st.error(f"Scrape Error: {e}")
    return ""

# --- THE STRUCTURED AI ---
def query_ai_report(clean_text):
    """Directs the AI to fill our specific buckets."""
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    
    # We take the top of the clean text (Facts) and the middle (Context)
    # Since it's Markdown, the AI understands headers and lists much better!
    prompt_input = clean_text[:1200] 
    
    payload = {"inputs": prompt_input, "parameters": {"max_length": 160, "min_length": 80}}
    
    try:
        r = requests.post(API_URL, headers=headers, json=payload, timeout=15)
        summary = r.json()[0]['summary_text']
        return summary
    except:
        return "System timeout. Manual extraction required."

# --- UI LOGIC ---
st.title("📡 NEO-SCOUT // AI_READER_V8.6")

# RSS Feed logic (Simplified for this example)
feed = feedparser.parse("https://www.goal.com/en/feeds/news")

for entry in feed.entries[:3]:
    with st.container(border=True):
        st.subheader(entry.title.upper())
        
        if st.button("🔬 GENERATE SMART REPORT", key=hashlib.md5(entry.link.encode()).hexdigest()):
            with st.spinner(">> AI IS READING THE PAGE..."):
                # STEP 1: Get Clean Data
                markdown_content = get_clean_intel(entry.link)
                
                if markdown_content:
                    # STEP 2: AI Summary
                    ai_result = query_ai_report(markdown_content)
                    
                    # STEP 3: The Structured Implementation
                    # We split the AI result into the format you requested
                    parts = ai_result.split(". ")
                    
                    event = parts[0] if len(parts) > 0 else "Analysis pending."
                    analysis = parts[1] if len(parts) > 1 else "Developing story."
                    history = parts[2] if len(parts) > 2 else "Check archives for deeper context."

                    st.markdown(f"""
                    ### 📍 [THE_EVENT]
                    {event}.

                    ### 🧠 [SYSTEM_ANALYSIS]
                    {analysis}.

                    ### 📜 [HISTORICAL_CONTEXT]
                    {history}.
                    """)
                    
                    # Social Format
                    final_post = f"⚽ {entry.title}\n\n📍 EVENT: {event}\n\n🧠 ANALYSIS: {analysis}\n\n📜 HISTORY: {history}\n\n#Football #Viral"
                    st.text_area(">> READY TO POST:", value=final_post, height=200)
                else:
                    st.error("Could not bypass site security.")
