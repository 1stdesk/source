import streamlit as st
import requests
import feedparser
import hashlib
from bs4 import BeautifulSoup
import time
import random

# --- CONFIG ---
st.set_page_config(page_title="NEO-SCOUT // VIRAL_POST_V8.3", page_icon="📡", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background-color: #050505; font-family: 'JetBrains Mono', monospace; }
    h1, h2, h3, p, span, div { color: #00ff41 !important; text-shadow: 0 0 5px #00ff41; }
    .stElementContainer div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #0a0a0a !important;
        border: 1px solid #00ff41 !important;
        box-shadow: 0 0 15px rgba(0, 255, 65, 0.2);
        padding: 20px; border-radius: 2px; margin-bottom: 20px;
    }
    .post-preview {
        background-color: #111; border: 1px dashed #00ff41;
        padding: 15px; color: white !important; font-family: sans-serif;
        line-height: 1.5; border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- VIRAL FORMATTER ---
def format_as_viral_post(title, summary, tags, link):
    """Formats the raw AI text into a high-engagement social media post."""
    emojis = ["🚨", "🔥", "⚽", "📊", "👀", "💎"]
    hook = random.choice(emojis)
    
    # Cleaning AI summary of any technical artifacts
    clean_summary = summary.replace("[AI_GEN]:", "").replace("[AUTO_GEN]:", "").strip()
    
    post = f"{hook} {title}\n\n"
    post += f"{clean_summary}\n\n"
    post += f"What are your thoughts? 👇\n\n"
    post += f"{tags}\n\n"
    post += f"🔗 Full Story: {link}"
    return post

# --- UPDATED AI CORE (Viral Persona) ---
def query_ai_viral(text):
    API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    if "HF_TOKEN" not in st.secrets: return "ERROR: TOKEN_NOT_FOUND"
    
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    # Adjusted parameters for more "punchy" output
    payload = {
        "inputs": text[:1024],
        "parameters": {"max_length": 120, "min_length": 50, "repetition_penalty": 1.2}
    }
    
    for _ in range(2):
        try:
            r = requests.post(API_URL, headers=headers, json=payload, timeout=15)
            res = r.json()
            if isinstance(res, list): return res[0]['summary_text']
            time.sleep(3)
        except: continue
    
    # Fallback that still looks like a post
    sentences = [s for s in text.split(". ") if len(s) > 30]
    return f"{sentences[0]}. {sentences[1]}."

# --- DATA & SCRAPING ---
def scrape_intel(url):
    try:
        r = requests.get(url, timeout=7, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.content, 'html.parser')
        img = soup.find("meta", property="og:image")
        junk = ["attendance:", "vs", "referee:", "copyright"]
        paras = [" ".join(p.get_text().split()) for p in soup.find_all('p')]
        clean_paras = [p for p in paras if len(p) > 80 and not any(j in p.lower() for j in junk)]
        return " ".join(clean_paras[:4]), (img["content"] if img else None)
    except: return "", None

@st.cache_data(ttl=300)
def get_randomized_feed():
    sources = [
        "https://www.goal.com/en/feeds/news", "https://www.skysports.com/rss/12040",
        "https://feeds.bbci.co.uk/sport/football/rss.xml", "https://www.football365.com/feed",
        "https://www.90min.com/posts.rss", "https://www.theguardian.com/football/rss"
    ]
    random.shuffle(sources)
    stream = []
    for url in sources[:5]:
        try:
            f = feedparser.parse(url)
            for entry in f.entries[:3]:
                stream.append({"id": hashlib.md5(entry.link.encode()).hexdigest(), "title": entry.title.upper(), "link": entry.link, "src": url.split('/')[2]})
        except: continue
    return stream

# --- UI MAIN ---
st.title("📡 NEO-SCOUT // VIRAL_READY_V8.3")

if st.button("🔄 RE-SCAN FOR VIRAL CONTENT"):
    st.cache_data.clear()
    st.rerun()

for item in get_randomized_feed():
    with st.container(border=True):
        st.write(f"NODE: {item['src'].upper()}")
        st.subheader(item['title'])
        
        if st.button("🚀 GENERATE_VIRAL_POST", key=item['id']):
            with st.spinner(">> CRAFTING_VIRAL_CONTENT..."):
                raw_text, image = scrape_intel(item['link'])
                if image: st.image(image, use_container_width=True)
                
                if len(raw_text) > 100:
                    summary = query_ai_viral(raw_text)
                    tags = f"#Football #SportsNews #{item['src'].split('.')[0]} #Viral"
                    
                    # Transform into a perfect post
                    final_post = format_as_viral_post(item['title'], summary, tags, item['link'])
                    
                    st.markdown("### >> PREVIEW_FOR_SOCIAL")
                    st.markdown(f'<div class="post-preview">{final_post.replace("\n", "<br>")}</div>', unsafe_allow_html=True)
                    
                    st.text_area(">> COPY_AND_PASTE_BELOW:", value=final_post, height=250)
                else:
                    st.error(">> SOURCE_PROTECTED")

st.markdown("---")
st.write(">> SYSTEM_READY // POST_MODE_ACTIVE")
