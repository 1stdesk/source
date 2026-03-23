import streamlit as st
import requests
import feedparser
import hashlib
from bs4 import BeautifulSoup
import time
import streamlit.components.v1 as components
from urllib.parse import urljoin
from duckduckgo_search import DDGS

# --- FUTURISTIC UI CONFIG ---
st.set_page_config(page_title="NEO-SCOUT v7.1", page_icon="📡", layout="wide")

# Custom CSS (unchanged)
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

# --- CACHED AI SUMMARY ---
@st.cache_data(ttl=3600, hash_funcs={str: lambda x: hashlib.md5(x.encode()).hexdigest()})
def get_ai_summary(text: str) -> str:
    API_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-cnn"
    if "HF_TOKEN" not in st.secrets:
        return "CRITICAL ERROR: ACCESS_TOKEN_NOT_FOUND"
    
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    payload = {
        "inputs": text[:1000],
        "parameters": {
            "do_sample": False,
            "max_length": 140,
            "min_length": 60,
            "repetition_penalty": 1.2,
            "length_penalty": 1.3
        }
    }
    for _ in range(3):
        try:
            response = requests.post(API_URL, headers=headers, json=payload, timeout=12)
            result = response.json()
            if isinstance(result, dict) and "estimated_time" in result:
                time.sleep(4)
                continue
            return result[0]['summary_text']
        except:
            continue
    return "SUMMARY_TIMEOUT"

# --- SOCCER FILTER ---
def is_soccer_story(title: str) -> bool:
    if not title:
        return False
    keywords = [
        "football", "soccer", "premier league", "epl", "champions league", "uefa",
        "bundesliga", "la liga", "serie a", "ligue 1", "world cup", "euro",
        "afcon", "fifa", "psl", "kaizer chiefs", "orlando pirates", "mamelodi sundowns",
        "man united", "man city", "liverpool", "arsenal", "chelsea", "tottenham"
    ]
    return any(kw in title.lower() for kw in keywords)

# --- VIDEO HELPERS ---
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

# --- CACHED WEB IMAGE SEARCH ---
@st.cache_data(ttl=1800)
def get_web_story_images(title: str):
    try:
        query = f'"{title}" soccer OR football (photo OR image OR gallery OR action OR highlight)'
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=5, safesearch="off"))
        urls = [r["image"] for r in results if r.get("image", "").startswith("http")]
        
        seen = set()
        unique = []
        for u in urls:
            if u not in seen:
                seen.add(u)
                unique.append(u)
        return unique[:3]
    except:
        return []

# --- CACHED STORY SCRAPING ---
@st.cache_data(ttl=1800)
def cached_scrape_story(url: str):
    try:
        r = requests.get(url, timeout=6, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.content, 'html.parser')
        
        paras = [p.get_text() for p in soup.find_all('p') if len(p.get_text()) > 60]
        raw_text = " ".join(paras[:5])
        
        original_images = []
        for prop in ["og:image", "og:image:secure_url", "twitter:image"]:
            meta = soup.find("meta", property=prop)
            if meta and meta.get("content"):
                u = meta["content"]
                if u.startswith("http") and u not in original_images:
                    original_images.append(u)
        
        for img in soup.find_all("img", src=True):
            src = img["src"]
            if src.startswith("//"): src = "https:" + src
            full_src = urljoin(url, src) if not src.startswith(('http://', 'https://')) else src
            bad = ["logo", "icon", "avatar", "pixel", "blank", "gif"]
            if (full_src not in original_images and 
                len(original_images) < 3 and 
                not any(b in full_src.lower() for b in bad)):
                original_images.append(full_src)
        
        return raw_text, original_images[:3]
    except:
        return "", []

# --- CACHED RSS FEED ---
@st.cache_data(ttl=300)
def get_live_stream():
    feeds = [
        ("NEWS24_SPORT", "https://feeds.24.com/articles/sport/featured/topstories/rss"),
        ("SABC_SPORT", "https://www.sabcnews.com/sabcnews/category/sport/feed/"),
        ("IOL_SPORT", "https://iol.co.za/rss/iol/sport"),
        ("MAILGUARDIAN_SPORT", "https://mg.co.za/section/sport/feed/"),
        ("GSPORT_SA", "https://gsport.co.za/feed/"),
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
    
    seen = {}
    for src_name, url in feeds:
        try:
            f = feedparser.parse(url)
            for entry in f.entries:
                if not is_soccer_story(entry.title):
                    continue
                link = entry.link
                pub_time = entry.get('published_parsed') or entry.get('updated_parsed') or time.gmtime(0)
                
                thumbnail = None
                if hasattr(entry, 'media_content') and entry.media_content:
                    for m in entry.media_content:
                        if m.get('url') and m.get('type', '').startswith('image'):
                            thumbnail = m['url']
                            break
                if not thumbnail and hasattr(entry, 'media_thumbnail') and entry.media_thumbnail:
                    thumbnail = entry.media_thumbnail[0].get('url')
                if not thumbnail and hasattr(entry, 'enclosure') and entry.enclosure:
                    if entry.enclosure.get('type', '').startswith('image'):
                        thumbnail = entry.enclosure['url']
                
                item = {
                    "id": hashlib.md5(link.encode()).hexdigest(),
                    "title": entry.title.upper(),
                    "link": link,
                    "src": src_name,
                    "thumbnail": thumbnail
                }
                if link not in seen or pub_time > seen[link][0]:
                    seen[link] = (pub_time, item)
        except:
            continue
    
    all_entries = [item for _, item in sorted(seen.values(), key=lambda x: x[0], reverse=True)][:60]
    return all_entries

# --- MAIN INTERFACE ---
st.title("📡 NEO-SCOUT // INTEL_AGGREGATOR_v7.1 – SPEED EDITION")
st.markdown("**SOCCER-ONLY • CACHED AI + ALWAYS SHOW WEB IMAGES + SCRAPING**")
st.markdown("---")

col_header, col_ref = st.columns([5, 1])
with col_ref:
    if st.button("🔄 REFRESH_LIST"):
        get_live_stream.clear()
        st.rerun()

search_buf = st.text_input(">> INITIALIZE_FILTER_QUERY:", "").upper()

news_stream = get_live_stream()
filtered_stream = [n for n in news_stream if search_buf in n['title']] if search_buf else news_stream

for item in filtered_stream:
    with st.container(border=True):
        st.write(f"SOURCE_NODE: {item['src']}")
        
        if item.get("thumbnail"):
            st.image(item["thumbnail"], use_container_width=True, caption="RSS THUMBNAIL")
        
        st.subheader(item['title'])
        
        c1, c2 = st.columns([1, 4])
        with c1:
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("RUN_DEEP_INTEL", key=f"ai_{item['id']}"):
                    with st.spinner(">> FAST DEEP SCAN (cached where possible)..."):
                        raw_text, original_images = cached_scrape_story(item['link'])
                        
                        # Web images ALWAYS fetched (as requested)
                        web_images = get_web_story_images(item['title'])
                        
                        # ORIGINAL IMAGES
                        if original_images:
                            st.write("**📸 IMAGES FROM ORIGINAL SOURCE**")
                            cols = st.columns(min(3, len(original_images)))
                            for idx, img_url in enumerate(original_images):
                                with cols[idx]:
                                    try:
                                        st.image(img_url, use_container_width=True)
                                    except:
                                        st.caption("Image failed to load")
                                    st.markdown(f"[📥]({img_url})")
                        else:
                            st.info("No images found in original article")
                        
                        # WEB IMAGES – always shown (even if original has good images)
                        if web_images:
                            st.write("**🌐 ADDITIONAL IMAGES FROM WEB SOURCES**")
                            cols = st.columns(min(3, len(web_images)))
                            for idx, img_url in enumerate(web_images):
                                with cols[idx]:
                                    try:
                                        st.image(img_url, use_container_width=True)
                                    except:
                                        st.caption("Image failed to load")
                                    st.markdown(f"[📥]({img_url})")
                        else:
                            st.info("No additional web images found")
                        
                        # CACHED AI SUMMARY
                        if len(raw_text) > 180:
                            report = get_ai_summary(raw_text)
                            st.markdown(f"""
                                <div class="intel-box">
                                    <strong>[AI SUMMARY – CACHED]</strong><br><br>
                                    {report}
                                </div
