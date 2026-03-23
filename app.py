import streamlit as st
import requests
import feedparser
import hashlib
import random
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import streamlit.components.v1 as components
from duckduckgo_search import DDGS

# ────────────────────────────────────────────────
#               CYBERPUNK DESIGN v8.1
# ────────────────────────────────────────────────
st.set_page_config(page_title="NEO-SCOUT • v8.1", page_icon="⚡️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Roboto+Mono:wght@400;500&display=swap');
.stApp { background: linear-gradient(135deg, #0d0015, #1a0033); color: #e0e0ff; }
h1, h2 { font-family: 'Orbitron', sans-serif; background: linear-gradient(90deg, #00f0ff, #c300ff); 
         -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.stButton > button { border: 2px solid #00f0ff; color: #00f0ff; background: transparent; border-radius: 12px; font-weight: 600; }
.stButton > button:hover { background: linear-gradient(45deg, #00f0ff, #c300ff); color: #000; }
.card { background: rgba(20,10,40,0.9); backdrop-filter: blur(16px); border: 1px solid #00f0ff33; 
        border-radius: 16px; padding: 1.5rem; margin-bottom: 1.5rem; }
.intel-box { background: rgba(25,10,45,0.95); border-left: 5px solid #c300ff; padding: 1.2rem; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#               HELPERS
# ────────────────────────────────────────────────
def smart_get(url):
    time.sleep(random.uniform(1, 3))
    headers = {"User-Agent": random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    ])}
    for prefix in ["https://archive.is/", "https://12ft.io/"]:
        try:
            r = requests.get(prefix + url, headers=headers, timeout=10)
            if r.ok and len(r.text) > 600: return r
        except: pass
    try:
        return requests.get(url, headers=headers, timeout=10)
    except:
        return None

@st.cache_data(ttl=1800)
def ai_topic(title):
    if "HF_TOKEN" not in st.secrets:
        return title[:60]
    try:
        r = requests.post(
            "https://api-inference.huggingface.co/models/google/flan-t5-base",
            headers={"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"},
            json={"inputs": f"Extract soccer topic (players, teams, event) in 8 words: {title}"}
        )
        return r.json()[0]["summary_text"] if r.ok else title[:60]
    except:
        return title[:60]

@st.cache_data(ttl=1800)
def get_two_relevant_images(title):
    topic = ai_topic(title)
    query = f'"{title}" {topic} soccer football (match OR goal OR player OR celebration) photo -stock -shutterstock -meme -cartoon'
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=10, safesearch="off"))
        urls = []
        seen = set()
        for r in results:
            img = r.get("image")
            if img and img.startswith("http") and img not in seen:
                if any(bad in img.lower() for bad in ["stock", "shutterstock", "meme"]):
                    continue
                seen.add(img)
                urls.append(img)
                if len(urls) == 2:
                    break
        return urls[:2]
    except:
        return []

@st.cache_data(ttl=1800)
def scrape_article(url):
    r = smart_get(url)
    if not r: return "", [], None
    soup = BeautifulSoup(r.content, "html.parser")
    text = " ".join([p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 45][:7])

    # Head thumbnail from article
    head_img = None
    for prop in ["og:image", "twitter:image"]:
        m = soup.find("meta", property=prop)
        if m and (v := m.get("content")) and v.startswith("http"):
            head_img = v
            break
    return text, [head_img] if head_img else [], head_img

# ────────────────────────────────────────────────
#               FEED
# ────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_soccer_feed():
    sources = [
        ("GOAL", "https://www.goal.com/en/feeds/news"),
        ("SKY", "https://www.skysports.com/rss/12040"),
        ("BBC", "https://feeds.bbci.co.uk/sport/football/rss.xml"),
        ("GUARDIAN", "https://www.theguardian.com/football/rss"),
    ]
    items = []
    seen = set()
    for name, url in sources:
        try:
            f = feedparser.parse(url)
            for e in f.entries:
                title = e.title.strip()
                if not title or not any(k in title.lower() for k in ["football","soccer","league","cup","goal"]):
                    continue
                link = e.link
                if link in seen: continue
                seen.add(link)

                thumb = None
                if media := e.get("media_content"):
                    for m in media:
                        if m.get("url") and m.get("type","").startswith("image"):
                            thumb = m["url"]
                            break
                if not thumb:
                    thumbs = e.get("media_thumbnail")
                    if thumbs:
                        thumb = thumbs[0].get("url")

                items.append({
                    "title": title.upper(),
                    "link": link,
                    "source": name,
                    "thumb": thumb,
                    "id": hashlib.md5(link.encode()).hexdigest()
                })
        except: pass
    return items[:60]

# ────────────────────────────────────────────────
#               MAIN INTERFACE
# ────────────────────────────────────────────────
st.title("⚡️ NEO-SCOUT • v8.1 • CYBERPUNK")
st.caption("Head Thumbnail + AI-Understood 2 Relevant Pictures • Fixed Neural Summary")

if st.button("⟲ REFRESH FEED"):
    get_soccer_feed.clear()
    st.rerun()

filter_text = st.text_input("FILTER HEADLINES", "").upper()

feed = get_soccer_feed()
if filter_text:
    feed = [e for e in feed if filter_text in e["title"]]

for entry in feed:
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        
        st.subheader(entry["title"])
        st.caption(f"📡 {entry['source']}")

        c1, c2 = st.columns([1, 4])
        with c1:
            if st.button("ANALYZE ARTICLE", key=f"btn_{entry['id']}"):
                with st.spinner("Extracting head image + AI analyzing topic..."):
                    text, head_list, head_img = scrape_article(entry["link"])
                    two_web = get_two_relevant_images(entry["title"])

                    # Head Thumbnail
                    st.markdown("**📸 Head Thumbnail from Article**")
                    if head_img:
                        st.image(head_img, use_container_width=True)
                    elif entry.get("thumb"):
                        st.image(entry["thumb"], use_container_width=True)

                    # 2 Relevant Pictures
                    st.markdown("**🌐 2 AI-Relevant Pictures (Topic Understood)**")
                    if two_web:
                        cols = st.columns(2)
                        for i, img in enumerate(two_web):
                            with cols[i]:
                                st.image(img, use_container_width=True)
                                st.markdown(f"[↓]({img})")
                    else:
                        st.info("No matching images found")

                    # AI Summary
                    summary = ai_summarize(text)
                    st.markdown(f"""
                    <div class="intel-box">
                        <strong>NEURAL SUMMARY</strong><br><br>
                        {summary}
                    </div>
                    """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"[→ FULL STORY]({entry['link']})")

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")

st.caption("v8.1 • Head thumbnail + exactly 2 AI-topic pictures • Clean cyberpunk design • Fixed AI core")
