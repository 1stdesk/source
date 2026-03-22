import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
from collections import Counter
import re

# --- CONFIG ---
st.set_page_config(page_title="AI Newsroom: Multi-Source Compiler", page_icon="⚽", layout="wide")

# --- STYLING ---
st.markdown("""
    <style>
    .compiler-box { 
        background-color: #001529; border: 2px solid #00ff41; 
        padding: 25px; border-radius: 15px; margin-bottom: 30px;
    }
    .source-pill {
        background-color: #00ff41; color: black; padding: 2px 10px;
        border-radius: 20px; font-size: 0.7rem; font-weight: bold; margin-right: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 20 MASTER SOURCES ---
MASTER_POOL = [
    ("Goal.com", "https://www.goal.com/en/feeds/news"),
    ("Sky Sports", "https://www.skysports.com/rss/12040"),
    ("BBC Sport", "http://newsrss.bbc.co.uk/rss/sportonline_uk_edition/football/rss.xml"),
    ("Soccer Laduma", "https://www.snl24.com/soccerladuma/rss"),
    ("Transfermarkt", "https://www.transfermarkt.com/rss/news"),
    ("ESPN FC", "https://www.espn.com/espn/rss/soccer/news"),
    ("The Guardian", "https://www.theguardian.com/football/rss"),
    ("90min", "https://www.90min.com/posts.rss"),
    ("Marca", "https://e00-marca.uecdn.es/rss/en/index.xml"),
    ("AS English", "https://en.as.com/rss/en/football/index.xml"),
    ("Football Italia", "https://football-italia.net/feed/"),
    ("Daily Mail", "https://www.dailymail.co.uk/sport/football/index.rss"),
    ("KickOff", "https://www.snl24.com/kickoff/rss"),
    ("Sowetan Live", "https://www.sowetanlive.co.za/sport/soccer/rss"),
    ("Ghana Soccernet", "https://ghanasoccernet.com/feed"),
    ("CaughtOffside", "https://www.caughtoffside.com/feed/"),
    ("TEAMtalk", "https://www.teamtalk.com/feed"),
    ("World Soccer", "https://www.worldsoccer.com/feed"),
    ("FourFourTwo", "https://www.fourfourtwo.com/rss.xml"),
    ("Daily Sun Soccer", "https://www.snl24.com/dailysun/sport/rss")
]

# --- INTELLIGENCE FUNCTIONS ---
def get_compiled_intel(urls):
    """Scrapes multiple URLs and merges content into one block."""
    combined_text = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    for url in urls[:3]: # Limit to top 3 sources to keep it fast
        try:
            r = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(r.content, 'html.parser')
            paras = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 100]
            combined_text.extend(paras[:2])
        except: continue
    return combined_text

def find_trending_topics(feed_items):
    """Identifies common themes across all 20 sources."""
    all_titles = " ".join([item['t'] for item in feed_items]).lower()
    words = re.findall(r'\w+', all_titles)
    # Filter out common 'stop words'
    stop_words = {'the', 'and', 'for', 'with', 'after', 'says', 'over', 'man', 'set', 'league', 'football', 'soccer'}
    meaningful_words = [w for w in words if len(w) > 3 and w not in stop_words]
    return Counter(meaningful_words).most_common(5)

# --- APP UI ---
st.title("⚽ AI MULTI-SOURCE COMPILER")
st.subheader("Synthesizing 20 sources into unified social reports")

if 'full_data' not in st.session_state:
    with st.spinner("Analyzing Global Landscape..."):
        all_news = []
        for name, url in MASTER_POOL:
            try:
                f = feedparser.parse(url)
                if f.entries:
                    all_news.append({"s": name, "t": f.entries[0].title, "l": f.entries[0].link})
            except: continue
        st.session_state.full_data = all_news

# --- TRENDING SECTION ---
trends = find_trending_topics(st.session_state.full_data)
st.write("### 📈 Current Trending Topics")
cols = st.columns(len(trends))
for i, (word, count) in enumerate(trends):
    if cols[i].button(f"{word.upper()} ({count} sources)"):
        st.session_state.current_query = word

# --- COMPILER ENGINE ---
query = st.text_input("Enter a Player, Team, or Topic to Compile:", st.session_state.get('current_query', ''))

if query:
    matches = [item for item in st.session_state.full_data if query.lower() in item['t'].lower()]
    
    if matches:
        st.success(f"Found {len(matches)} sources discussing '{query}'")
        if st.button(f"🚀 COMPILE MASTER REPORT ON '{query.upper()}'"):
            with st.spinner("Extracting and cross-referencing content..."):
                sources_used = [m['s'] for m in matches]
                links_used = [m['l'] for m in matches]
                titles_used = [m['t'] for m in matches]
                
                deep_content = get_compiled_intel(links_used)
                
                # Create Compiled Facebook Post
                source_tags = " ".join([f"#{s.replace(' ', '')}" for s in sources_used])
                bullet_points = "\n".join([f"✅ {p[:180]}..." for p in deep_content[:5]])
                
                master_post = (
                    f"🔥 MULTI-SOURCE UPDATE: {query.upper()} 🔥\n\n"
                    f"We have analyzed reports from {len(matches)} major outlets including {', '.join(sources_used[:3])}.\n\n"
                    f"📝 KEY COMPILATION:\n"
                    f"{bullet_points}\n\n"
                    f"🌐 CITED SOURCES:\n" + "\n".join([f"- {t}" for t in titles_used[:3]]) + 
                    f"\n\n👉 Stay tuned for more compiled updates!\n\n"
                    f"#SoccerNews #CompiledReport #FootballIntel {source_tags}"
                )
                
                st.markdown('<div class="compiler-box">', unsafe_allow_html=True)
                st.markdown("### 📋 Unified Social Media Post")
                st.code(master_post, language="markdown")
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("No matches found in the current 20 sources for that topic.")

# --- RAW FEED LIST ---
st.write("---")
st.write("### 🗄️ Raw Multi-Source Feed")
for item in st.session_state.full_data:
    st.markdown(f'<span class="source-pill">{item["s"]}</span> {item["t"]}', unsafe_allow_html=True)
