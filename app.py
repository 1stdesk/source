import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
import hashlib

# --- PAGE CONFIG ---
st.set_page_config(page_title="Soccer Scout AI v5.0", page_icon="⚽")

# --- AI SETUP (The "Task-Agnostic" Way) ---
@st.cache_resource
def load_summarizer():
    try:
        model_id = "sshleifer/distilbart-cnn-6-6"
        # Manually load to bypass the "Unknown task" error
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_id)
        
        # We tell the pipeline EXACTLY what model and tokenizer to use
        return pipeline(
            "summarization", 
            model=model, 
            tokenizer=tokenizer, 
            framework="pt"
        )
    except Exception as e:
        st.sidebar.error(f"AI Boot Error: {e}")
        return None

# Load the engine
ai_scout = load_summarizer()

# --- SCRAPER ---
def get_news():
    feeds = ["https://www.goal.com/en/feeds/news", "https://www.skysports.com/rss/12040"]
    data = []
    for f_url in feeds:
        feed = feedparser.parse(f_url)
        for entry in feed.entries[:5]:
            data.append({
                "id": hashlib.md5(entry.link.encode()).hexdigest(),
                "title": entry.title,
                "link": entry.link,
                "source": f_url.split('/')[2]
            })
    return data

def scrape_content(url):
    try:
        r = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.content, 'html.parser')
        text = " ".join([p.get_text() for p in soup.find_all('p')[:3]])
        img = soup.find("meta", property="og:image")
        return text, (img["content"] if img else None)
    except: return "", None

# --- UI LAYOUT ---
st.title("⚽ Soccer Scout AI")

if 'feed' not in st.session_state:
    st.session_state.feed = get_news()

for item in st.session_state.feed:
    with st.container(border=True):
        st.subheader(item['title'])
        st.caption(f"Source: {item['source']}")
        
        if st.button("Analyze Story", key=item['id']):
            if ai_scout:
                with st.spinner("AI is scouting the details..."):
                    raw_text, img_url = scrape_content(item['link'])
                    if img_url: st.image(img_url, width=400)
                    
                    if len(raw_text) > 100:
                        # Generation parameters to ensure quality
                        summary = ai_scout(raw_text[:1024], max_length=50, min_length=20, do_sample=False)
                        st.success(f"**The Scoop:** {summary[0]['summary_text']}")
                    else:
                        st.warning("Article too short for AI analysis.")
            else:
                st.error("AI Engine is currently offline. Check logs.")
        
        st.markdown(f"[Read full story]({item['link']})")
