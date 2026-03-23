import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random
from transformers import pipeline  # <--- New Import

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Pro Soccer Scout AI v3", page_icon="⚽", layout="wide")

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
        border: 1px solid #30363d; margin-bottom: 25px;
    }
    .source-tag { color: #58a6ff; font-weight: bold; font-size: 0.85rem; }
    .headline-link { color: #f0f6fc; font-weight: 600; text-decoration: none; font-size: 1.3rem; }
    </style>
    """, unsafe_allow_html=True)

# --- AI MODEL LOADING ---
@st.cache_resource
def load_qa_pipeline():
    # Using roberta-large fine-tuned on SQuAD2.0 for extractive QA
    return pipeline("question-answering", model="deepset/roberta-large-squad2")

qa_model = load_qa_pipeline()

# --- SOURCE POOL ---
MASTER_POOL = [
    ("Goal.com", "https://www.goal.com/en/feeds/news"),
    ("Sky Sports", "https://www.skysports.com/rss/12040"),
    ("BBC Sport", "https://push.api.bbci.co.uk/morph/items?page=1&limit=10&feed=football"),
    ("Transfermarkt", "https://www.transfermarkt.com/rss/news")
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
    return results

def get_full_text(url):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
        soup = BeautifulSoup(r.content, 'html.parser')
        paras = [p.get_text() for p in soup.find_all('p')]
        return " ".join(paras[:5]) # Get first 5 paragraphs for context
    except: return ""

# --- APP LAYOUT ---
tab1, tab2 = st.tabs(["📢 Smart News Feed", "💬 RoBERTa AI Scout"])

if 'news_feed' not in st.session_state:
    st.session_state.news_feed = fetch_stories()

with tab1:
    st.title("⚽ GLOBAL SOCCER AGGREGATOR")
    for i, item in enumerate(st.session_state.news_feed):
        st.markdown(f'''
            <div class="news-card">
                <div class="source-tag">{item["s"]}</div>
                <a href="{item["l"]}" target="_blank" class="headline-link">{item["t"]}</a>
            </div>
        ''', unsafe_allow_html=True)

with tab2:
    st.header("🤖 RoBERTa-Large Intelligence")
    st.info("The AI will scan the current top headlines to answer your question.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("e.g., Who is being linked with a transfer?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("RoBERTa is analyzing the field..."):
                # 1. Build context from current headlines
                context = ". ".join([n['t'] for n in st.session_state.news_feed])
                
                # 2. Run Extractive QA
                try:
                    result = qa_model(question=prompt, context=context)
                    
                    # 3. Handle low confidence scores
                    if result['score'] > 0.01:
                        response = f"**Answer:** {result['answer']}\n\n*(Confidence: {result['score']:.2f})*"
                    else:
                        response = "I couldn't find a definitive answer in the current headlines. Try being more specific about a player or team."
                except Exception as e:
                    response = "I encountered an error processing that scout report."

            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
