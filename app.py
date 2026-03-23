import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random
import torch # Explicitly import torch to help transformers find the backend
from transformers import pipeline

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Pro Soccer Scout AI v3.1", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; background-color: #161b22; border-radius: 10px; color: white; 
    }
    .stTabs [aria-selected="true"] { background-color: #238636; color: white; font-weight: bold; }
    .news-card { 
        background-color: #161b22; padding: 25px; border-radius: 12px; 
        border: 1px solid #30363d; margin-bottom: 20px;
    }
    .source-tag { color: #58a6ff; font-weight: bold; font-size: 0.85rem; margin-bottom: 5px; }
    .headline-link { color: #f0f6fc; font-weight: 600; text-decoration: none; font-size: 1.2rem; }
    .headline-link:hover { color: #238636; }
    </style>
    """, unsafe_allow_html=True)

# --- AI MODEL LOADING (The Fix) ---
@st.cache_resource
def load_qa_pipeline():
    try:
        # Forcing framework="pt" (PyTorch) fixes the KeyError: 'question-answering'
        return pipeline(
            "question-answering", 
            model="deepset/roberta-large-squad2", 
            framework="pt"
        )
    except Exception as e:
        st.error(f"Scout Intelligence Error: {e}")
        return None

qa_model = load_qa_pipeline()

# --- SOURCE POOL ---
MASTER_POOL = [
    ("Goal.com", "https://www.goal.com/en/feeds/news"),
    ("Sky Sports", "https://www.skysports.com/rss/12040"),
    ("BBC Sport", "https://push.api.bbci.co.uk/morph/items?page=1&limit=10&feed=football"),
    ("Transfermarkt", "https://www.transfermarkt.com/rss/news"),
    ("90min", "https://www.90min.com/posts.rss")
]

# --- UTILITY FUNCTIONS ---
@st.cache_data(ttl=600)
def fetch_stories():
    results = []
    for name, url in MASTER_POOL:
        try:
            f = feedparser.parse(url)
            for entry in f.entries[:5]:
                results.append({'s': name, 't': entry.title, 'l': entry.link})
        except: continue
    random.shuffle(results)
    return results

# --- SIDEBAR ---
st.sidebar.title("🔍 Scout Filters")
if st.sidebar.button("🔄 Clear Cache & Refresh"):
    st.cache_data.clear()
    st.rerun()

# --- APP LAYOUT ---
tab1, tab2 = st.tabs(["📢 Smart News Feed", "💬 RoBERTa AI Scout"])

if 'news_feed' not in st.session_state:
    st.session_state.news_feed = fetch_stories()

with tab1:
    st.title("⚽ GLOBAL SOCCER AGGREGATOR")
    
    search_q = st.text_input("Search headlines...", "")
    
    filtered_news = [n for n in st.session_state.news_feed if search_q.lower() in n['t'].lower()]
    
    for item in filtered_news:
        st.markdown(f'''
            <div class="news-card">
                <div class="source-tag">{item["s"]}</div>
                <a href="{item["l"]}" target="_blank" class="headline-link">{item["t"]}</a>
            </div>
        ''', unsafe_allow_html=True)

with tab2:
    st.header("🤖 RoBERTa-Large Intelligence")
    
    if qa_model is None:
        st.warning("AI Model failed to initialize. Please check logs for memory or framework issues.")
    else:
        st.info("Ask a question about the current news (e.g., 'Who is injured?' or 'Which club is signing players?')")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        if prompt := st.chat_input("Ask the Scout..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                # Combine all headlines to create the "Context" for the AI to read
                context = ". ".join([n['t'] for n in st.session_state.news_feed])
                
                with st.spinner("RoBERTa scanning headlines..."):
                    try:
                        result = qa_model(question=prompt, context=context)
                        if result['score'] > 0.005:
                            response = f"**Answer:** {result['answer'].capitalize()}\n\n*(Confidence: {result['score']:.2%})*"
                        else:
                            response = "I couldn't find a clear answer in the current headlines. Try asking about a specific team or player mentioned in the feed."
                    except:
                        response = "I'm having trouble processing that context right now."

                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})
