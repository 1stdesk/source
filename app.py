import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
from newspaper import Article
import torch
from transformers import pipeline

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Pro Soccer Scout AI v4", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; background-color: #161b22; border-radius: 10px; color: white; 
    }
    .stTabs [aria-selected="true"] { background-color: #238636; color: white; font-weight: bold; }
    .scout-card { 
        background-color: #161b22; padding: 25px; border-radius: 15px; 
        border: 1px solid #30363d; margin-bottom: 25px;
    }
    .summary-box {
        background-color: #0d1117; padding: 15px; border-left: 4px solid #238636;
        margin: 15px 0; font-size: 0.95rem; line-height: 1.6;
    }
    .img-grid { display: flex; gap: 10px; margin-top: 15px; }
    .source-tag { color: #58a6ff; font-weight: bold; font-size: 0.8rem; text-transform: uppercase; }
    .headline { color: #f0f6fc; font-weight: 700; font-size: 1.5rem; text-decoration: none; }
    </style>
    """, unsafe_allow_html=True)

# --- AI MODELS ---
@st.cache_resource
def load_ai_models():
    # Summarizer for the article "Scoop"
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn", framework="pt")
    # RoBERTa for the Interactive QA
    qa_model = pipeline("question-answering", model="deepset/roberta-large-squad2", framework="pt")
    return summarizer, qa_model

try:
    summarizer, qa_model = load_ai_models()
except Exception as e:
    st.error("Intelligence systems offline. Memory limit likely exceeded.")
    st.stop()

# --- UTILITY: DEEP SCRAPING ---
def get_deep_scout_report(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        
        # Get top 3 images (filtering out tiny icons)
        all_imgs = [img for img in article.images if "icon" not in img.lower() and "logo" not in img.lower()]
        top_3_imgs = all_imgs[:3]
        
        # Generate AI Summary (limit input text to 1024 tokens for BART)
        raw_text = article.text[:2000]
        summary = summarizer(raw_text, max_length=130, min_length=30, do_sample=False)[0]['summary_text']
        
        return {
            "summary": summary,
            "imgs": top_3_imgs,
            "full_text": article.text
        }
    except:
        return None

# --- SOURCE POOL ---
SOURCES = [
    ("Goal.com", "https://www.goal.com/en/feeds/news"),
    ("BBC Football", "https://push.api.bbci.co.uk/morph/items?page=1&limit=10&feed=football"),
    ("Sky Sports", "https://www.skysports.com/rss/12040"),
    ("Transfermarkt", "https://www.transfermarkt.com/rss/news")
]

@st.cache_data(ttl=600)
def fetch_news():
    feed_data = []
    for name, url in SOURCES:
        try:
            f = feedparser.parse(url)
            for entry in f.entries[:3]:
                feed_data.append({'s': name, 't': entry.title, 'l': entry.link})
        except: continue
    return feed_data

# --- APP INTERFACE ---
tab1, tab2 = st.tabs(["🕵️ Deep Scout Feed", "💬 AI Intelligence Chat"])

if 'news_feed' not in st.session_state:
    st.session_state.news_feed = fetch_news()

with tab1:
    st.title("⚽ PRO SCOUT INTELLIGENCE v4")
    
    for i, item in enumerate(st.session_state.news_feed):
        with st.container():
            st.markdown(f'<div class="source-tag">{item["s"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<a class="headline" href="{item["l"]}">{item["t"]}</a>', unsafe_allow_html=True)
            
            if st.button(f"🔍 RUN DEEP SCOUT REPORT", key=f"scout_{i}"):
                with st.spinner("Analyzing article and fetching visuals..."):
                    data = get_deep_scout_report(item['l'])
                    if data:
                        st.markdown(f'<div class="summary-box"><b>AI SUMMARY:</b><br>{data["summary"]}</div>', unsafe_allow_html=True)
                        
                        # Display 3 Images
                        cols = st.columns(3)
                        for idx, img_url in enumerate(data['imgs']):
                            cols[idx].image(img_url, use_container_width=True)
                            
                        # Store context for the Chat Tab
                        st.session_state.current_context = data['full_text']
                        st.success("Article context loaded into AI Chat!")
                    else:
                        st.error("Could not bypass site security to scrape full article.")
            st.markdown("---")

with tab2:
    st.header("🤖 RoBERTa Interactive Scout")
    
    context = st.session_state.get('current_context', ". ".join([n['t'] for n in st.session_state.news_feed]))
    
    if 'current_context' in st.session_state:
        st.success("✅ Currently analyzing the last 'Deep Scout' article.")
    else:
        st.info("ℹ️ Analyzing general headlines. Use 'Deep Scout' on an article for better answers.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("What are the specific details of this transfer/injury?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("RoBERTa checking the facts..."):
                result = qa_model(question=prompt, context=context)
                if result['score'] > 0.001:
                    response = f"**Scout Finding:** {result['answer']}\n\n*(Certainty: {result['score']:.2%})*"
                else:
                    response = "I couldn't find that specific detail in the text provided."
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
