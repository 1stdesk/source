import streamlit as st
import requests
import feedparser
import hashlib
from bs4 import BeautifulSoup
import time
import streamlit.components.v1 as components

# --- FUTURISTIC UI CONFIG ---
st.set_page_config(page_title="NEO-SCOUT v7.0", page_icon="📡", layout="wide")

# Custom CSS for Futuristic/Terminal look
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');

    .stApp { background-color: #050505; font-family: 'JetBrains Mono', monospace; }
    h1, h2, h3, p, span, div { color: #00ff41 !important; text-shadow: 0 0 5px #00ff41; }
    .stElementContainer div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #0a0a0a !important; border: 1px solid #00ff41 !important;
        box-shadow: 0 0 15px rgba(0, 255, 65, 0.2); padding: 20px; border-radius: 2px; margin-bottom: 20px;
    }
    .stButton>button {
        background-color: transparent !important; color: #00ff41 !important;
        border: 1px solid #00ff41 !important; font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase; letter-spacing: 2px; transition: 0.3s; border-radius: 0px;
    }
    .stButton>button:hover { background-color: #00ff41 !important; color: #000 !important; box-shadow: 0 0 20px #00ff41; }
    .intel-box {
        background-color: #001a00; border-left: 4px solid #00ff41; padding: 15px;
        margin: 10px 0; font-size: 0.95rem; color: #d1ffd1 !important; line-height: 1.6;
    }
    .stTextInput input { background-color: #000 !important; color: #00ff41 !important; border: 1px solid #00ff41 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- AI CORE ---
def query_ai_deep(text):
    API_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-cnn"
    if "HF_TOKEN" not in st.secrets:
        return "CRITICAL ERROR: ACCESS_TOKEN_NOT_FOUND"
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    payload = {
        "inputs": text[:1500],
        "parameters": {"do_sample": False, "max_length": 180, "min_length": 90,
                       "repetition_penalty": 1.3, "length_penalty": 1.5}
    }
    for i in range(3):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=15)
            result = response.json()
            if isinstance(result, dict) and "estimated_time" in result:
                time.sleep(5); continue
            return result[0]['summary_text']
        except: continue
    return "SYSTEM_TIMEOUT: MODEL_FAILURE"

# --- SOCCER-ONLY FILTER ---
def is_soccer_story(title: str) -> bool:
    if not title:
        return False
    keywords = [
        "football", "soccer", "premier league", "epl", "champions league", "uefa",
        "bundesliga", "la liga", "serie a", "ligue 1", "world cup", "euro",
        "afcon", "fifa", "psl", "kaizer chiefs", "orlando pirates", "mamelodi sundowns",
        "man united", "man city", "liverpool", "arsenal", "chelsea", "tottenham"
    ]
    title_lower = title.lower()
    return any(kw in title_lower for kw in keywords)

# --- VIDEO DETECTION HELPER ---
def extract_video_info(url):
    try:
        r = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.content, 'html.parser')
        og_video = soup.find("meta", property="og:video") or soup.find("meta", property="og:video:secure_url")
        if og_video and og_video.get("content"):
            vurl = og_video["content"]
            if "youtube.com" in vurl.lower() or "youtu.be" in vurl.lower():
                return vurl, "youtube"
            return vurl, "direct"
        iframe = soup.find("iframe", src=lambda x: x and ("youtube.com/embed" in x or "youtu.be" in x))
        if iframe and iframe.get("src"):
            return iframe["src"], "youtube"
        video_tag = soup.find("video")
        if video_tag:
            source = video_tag.find("source")
            if source and source.get("src"):
                return source["src"], "direct"
        return None, None
    except:
        return None, None

def extract_youtube_id(video_url):
    if not video_url: return None
    if "embed/" in video_url: return video_url.split("embed/")[-1].split("?")[0].split("&")[0]
    if "watch?v=" in video_url: return video_url.split("watch?v=")[-1].split("&")[0]
    if "youtu.be/" in video_url: return video_url.split("youtu.be/")[-1].split("?")[0]
    return None

# --- 20 SOURCES → SOCCER-ONLY + MIXED BY LATEST + DEDUPLICATED ---
@st.cache_data(ttl=300)
def get_live_stream():
    feeds = [
        # 5 BEST SOUTH AFRICAN
        ("NEWS24_SPORT", "https://feeds.24.com/articles/sport/featured/topstories/rss"),
        ("SABC_SPORT", "https://www.sabcnews.com/sabcnews/category/sport/feed/"),
        ("IOL_SPORT", "https://iol.co.za/rss/iol/sport"),
        ("MAILGUARDIAN_SPORT", "https://mg.co.za/section/sport/feed/"),
        ("GSPORT_SA", "https://gsport.co.za/feed/"),
        
        # 15 POPULAR WORLDWIDE
        ("GOAL", "https://www.goal.com/en/feeds/news"),
        ("SKY_SPORTS", "https://www.skysports.com/rss/12040"),
        ("GUARDIAN_FOOTBALL", "https://www.theguardian.com/football/rss"),
        ("BBC_SPORT", "https://feeds.bbci.co.uk/sport/rss.xml"),
        ("ESPN", "https://www.espn.com/espn/rss/news"),
        ("YAHOO_SPORTS", "https://sports.yahoo.com/general/news/rss/"),
        ("CNN_SPORT", "http://rss.cnn.com/rss/edition_sport.rss"),
        ("FOX_SPORTS", "http://feeds.foxnews.com/foxnews/sports"),
        ("NYTIMES_SPORTS", "http://rss.nytimes.com/services/xml/rss/nyt/Sports.xml"),
        ("BLEACHER_REPORT", "https://bleacherreport.com/rss"),
        ("TALKSPORT", "https://talksport.com/rss/sports-news/all/feed"),
        ("SPORTS_ILLUSTRATED", "http://www.si.com/rss/si_topstories.rss"),
        ("CBS_SPORTS", "https://www.cbssports.com/rss/headlines/"),
        ("GUARDIAN_SPORT", "https://www.theguardian.com/sport/rss"),
        ("BBC_FOOTBALL", "https://feeds.bbci.co.uk/sport/football/rss.xml")
    ]
    
    seen = {}  # link → (pub_time, item)  → automatic deduplication
    for src_name, url in feeds:
        try:
            f = feedparser.parse(url)
            for entry in f.entries:
                if not is_soccer_story(entry.title):
                    continue
                link = entry.link
                pub_time = entry.get('published_parsed') or entry.get('updated_parsed') or time.gmtime(0)
                item = {
                    "id": hashlib.md5(link.encode()).hexdigest(),
                    "title": entry.title.upper(),
                    "link": link,
                    "src": src_name
                }
                # Keep the version with the newest publish time if duplicate appears
                if link not in seen or pub_time > seen[link][0]:
                    seen[link] = (pub_time, item)
        except:
            continue
    
    # Sort by latest time across ALL 20 sources
    all_entries = list(seen.values())
    all_entries.sort(key=lambda x: x[0], reverse=True)
    
    stream = [item for _, item in all_entries[:60]]
    return stream

def scrape_intel(url):
    try:
        r = requests.get(url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.content, 'html.parser')
        img = soup.find("meta", property="og:image")
        paras = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60]
        return " ".join(paras[:5]), (img["content"] if img else None)
    except: 
        return "", None

# --- MAIN INTERFACE ---
st.title("📡 NEO-SCOUT // INTEL_AGGREGATOR_V7")
st.markdown("**SOCCER-ONLY • 20 SOURCES MIXED BY LATEST • AI + VIDEO PLAY/DOWNLOAD**")
st.markdown("---")

col_header, col_ref = st.columns([5, 1])
with col_ref:
    if st.button("🔄 REFRESH_LIST"):
        st.cache_data.clear()
        st.rerun()

search_buf = st.text_input(">> INITIALIZE_FILTER_QUERY:", "").upper()

news_stream = get_live_stream()
filtered_stream = [n for n in news_stream if search_buf in n['title']] if search_buf else news_stream

for item in filtered_stream:
    with st.container(border=True):
        st.write(f"SOURCE_NODE: {item['src']}")
        st.subheader(item['title'])
        
        c1, c2 = st.columns([1, 4])
        with c1:
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("RUN_DEEP_INTEL", key=f"ai_{item['id']}"):
                    with st.spinner(">> DECRYPTING_AND_SUMMARIZING..."):
                        raw_text, image = scrape_intel(item['link'])
                        if image: 
                            st.image(image, use_container_width=True)
                        if len(raw_text) > 200:
                            report = query_ai_deep(raw_text)
                            st.markdown(f"""
                                <div class="intel-box">
                                    <strong>[AI_SCOUT_DEEP_REPORT]</strong><br><br>
                                    {report}
                                </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.write(">> ERROR: DATA_PACKET_TOO_SMALL")
            
            with col_btn2:
                if st.button("🎥 SCAN_VIDEO", key=f"vid_{item['id']}"):
                    with st.spinner(">> SCANNING_FOR_VIDEO..."):
                        video_url, video_type = extract_video_info(item['link'])
                        if video_url:
                            if video_type == "youtube":
                                vid_id = extract_youtube_id(video_url)
                                if vid_id:
                                    st.success("✅ YOUTUBE HIGHLIGHT FOUND")
                                    components.html(
                                        f'<iframe width="100%" height="400" '
                                        f'src="https://www.youtube.com/embed/{vid_id}" '
                                        f'frameborder="0" allowfullscreen></iframe>',
                                        height=420
                                    )
                                    st.markdown(f"[📥 Open on YouTube & Download]({video_url})")
                            else:
                                st.success("✅ DIRECT VIDEO FOUND")
                                st.video(video_url)
                                st.markdown(f"[📥 RIGHT-CLICK → SAVE VIDEO]({video_url})")
                        else:
                            st.info("No embedded video detected on this story")
        
        with c2:
            st.markdown(f"[>> ACCESS_FULL_LINK]({item['link']})")

st.markdown("---")
st.write(">> END_OF_STREAM • SOCCER-ONLY • MIXED LATEST STORIES FROM 20 SOURCES • VIDEO READY")
