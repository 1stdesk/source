import streamlit as st
import requests
from bs4 import BeautifulSoup
import feedparser
import hashlib
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline

# --- PAGE CONFIG ---
st.set_page_config(page_title="Soccer Scout AI v3.2", page_icon="⚽")

# --- NEW HARDENED AI LOADING ---
@st.cache_resource
def load_summarizer():
    try:
        model_name = "sshleifer/distilbart-cnn-12-6"
        
        # Explicitly load tokenizer and model
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        
        # Create the pipeline using the explicit objects
        # We use 'text-generation' logic if 'summarization' is missing, 
        # but usually, passing the model directly fixes the task mapping.
        pipe = pipeline(
            task="summarization", 
            model=model, 
            tokenizer=tokenizer,
            device=-1 # CPU
        )
        return pipe
    except Exception as e:
        # Fallback: Try to load as a generic task if 'summarization' string fails
        try:
            return pipeline(model="sshleifer/distilbart-cnn-12-6", device=-1)
        except:
            st.error(f"Critical AI Loading Failure: {e}")
            return None

summarizer = load_summarizer()

# --- THE REST OF YOUR APP ---
st.title("⚽ Soccer Scout AI")

# (Scraper logic remains the same)
class SoccerScraper:
    def fetch_rss(self):
        feeds = ["https://www.goal.com/en/feeds/news", "https://www.skysports.com/rss/12040"]
        results = []
        for url in feeds:
            f = feedparser.parse(url)
            for entry in f.entries[:5]:
                results.append({"id": hashlib.md5(entry.link.encode()).hexdigest(), "title": entry.title, "link": entry.link, "source": url.split('/')[2]})
        return results

    def get_full_text(self, url):
        try:
            r = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(r.content, 'html.parser')
            img = soup.find("meta", property="og:image")
            paras = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60]
            return " ".join(paras[:3]), (img["content"] if img else None)
        except: return "", None

scraper = SoccerScraper()
if 'news' not in st.session_state:
    st.session_state.news = scraper.fetch_rss()

for item in st.session_state.news:
    with st.expander(item['title']):
        if st.button("Analyze with AI", key=item['id']):
            if summarizer:
                text, img = scraper.get_full_text(item['link'])
                if img: st.image(img)
                if len(text) > 100:
                    # Explicitly setting generation parameters for DistilBART
                    summary = summarizer(text[:1024], max_length=60, min_length=20, do_sample=False)
                    st.info(f"**AI Summary:** {summary[0]['summary_text']}")
                else:
                    st.warning("Article too short for analysis.")
            else:
                st.error("AI Engine is offline. Check Requirements.txt for 'torch'.")
