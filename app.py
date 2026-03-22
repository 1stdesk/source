import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random

# --- CONFIG & STYLING ---
st.set_page_config(page_title="Pro Soccer Scout AI", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #050505; color: white; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; background-color: #121212; border-radius: 10px; color: white; 
    }
    .stTabs [aria-selected="true"] { background-color: #00ff41; color: black; font-weight: bold; }
    .news-card { 
        background-color: #121212; padding: 20px; border-radius: 15px; 
        border: 1px solid #333; margin-bottom: 20px; 
    }
    .source-tag { color: #00ff41; font-weight: bold; font-size: 0.8rem; text-transform: uppercase; }
    .headline-link { color: white; font-weight: bold; text-decoration: none; font-size: 1.2rem; }
    .summary-box { 
        background-color: #000; padding: 15px; border-radius: 10px; 
        border-left: 4px solid #00ff41; line-height: 1.6; color: #d1d1d1;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SOURCE POOL (From your soccer_news_sources_formatted.txt) ---
# [cite: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
MASTER_POOL = [
    ("Goal.com", "https://www.goal.com"), ("Sky Sports", "https://www.skysports.com/football"),
    ("BBC Sport", "https://www.bbc.com/sport/football"), ("Soccer Laduma", "https://www.soccerladuma.co.za"),
    ("KickOff", "https://www.kickoff.com"), ("ESPN FC", "https://www.espn.com/soccer/"),
    ("The Guardian", "https://www.theguardian.com/football"), ("90min", "https://www.90min.com"),
    ("Transfermarkt", "https://www.transfermarkt.com"), ("Marca", "https://www.marca.com/en/football.html")
]

# --- UTILITY FUNCTIONS ---
def get_3_para_summary(url):
    """Scrapes an article and formats it into a 3-paragraph summary."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.content, 'html.parser')
        
        # Extract all paragraphs with substantial text
        paras = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 120]
        
        if len(paras) < 3:
            return "Unable to extract enough detail for a 3-paragraph summary. Please check the source link directly."

        # Organize into 3 specific sections
        total = len(paras)
        para1 = " ".join(paras[:max(1, total // 3)])
        para2 = " ".join(paras[max(1, total // 3):max(2, (2 * total) // 3)])
        para3 = " ".join(paras[max(2, (2 * total) // 3):])

        summary = f"**1. Overview:** {para1[:400]}...\n\n"
        summary += f"**2. Key Analysis:** {para2[:450]}...\n\n"
        summary += f"**3. Outlook:** {para3[:400]}..."
        return summary
    except Exception as e:
        return f"Error connecting to source: {str(e)}"

def fetch_20():
    """Simulates fetching from random sources in your pool."""
    random_sources = random.sample(MASTER_POOL, min(len(MASTER_POOL), 20))
    # In a real app, you would use feedparser here to get live RSS entries
    # This is a placeholder for demonstration
    return [{'s': s[0], 't': f"Latest Update from {s[0]}", 'l': s[1]} for s in random_sources]

# --- APP LAYOUT ---
tab1, tab2 = st.tabs(["📢 Social News Feed", "💬 Chat with Scout"])

with tab1:
    st.title("⚽ GLOBAL SOCCER AGGREGATOR")
    if st.button("🔄 REFRESH: SCAN NEW SOURCES"):
        st.session_state.news_feed = fetch_20()

    if 'news_feed' not in st.session_state:
        st.session_state.news_feed = fetch_20()

    for i, item in enumerate(st.session_state.news_feed, 1):
        st.markdown(f'<div class="news-card">', unsafe_allow_html=True)
        st.markdown(f'<div class="source-tag">{i}. {item["s"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<a href="{item["l"]}" target="_blank" class="headline-link">{item["t"]}</a>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.header("🤖 AI Scout Assistant")
    st.caption("Ask me to 'summarize' any story from your feed!")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Welcome! You can ask me to 'summarize source 1' or ask about a specific team."}]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Summarize source 1..."):
        st.chat_message("user").markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        query = prompt.lower()
        response = ""

        # Logic for 3-paragraph summary command
        if "summarize source" in query:
            try:
                index = int(query.split("source")[-1].strip()) - 1
                if 0 <= index < len(st.session_state.news_feed):
                    target = st.session_state.news_feed[index]
                    with st.spinner(f"Scraping {target['s']} for a detailed summary..."):
                        detail_text = get_3_para_summary(target['l'])
                        response = f"### Detailed Report: {target['t']}\n\n{detail_text}"
                else:
                    response = "Invalid source number. Please choose a number from the current feed."
            except:
                response = "Please use the format: 'Summarize source 1'."
        
        # General search logic
        else:
            matches = [n for n in st.session_state.news_feed if query in n['t'].lower()]
            if matches:
                response = "I found these matches. Ask me to 'summarize source [number]' for a 3-paragraph report:\n\n"
                for m in matches:
                    response += f"- {m['s']}: {m['t']}\n"
            else:
                response = "I couldn't find a direct match. Try asking to 'summarize source 1'."

        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
