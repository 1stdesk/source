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
#               UI SETUP
# ────────────────────────────────────────────────
st.set_page_config(page_title="NEO-SCOUT v7.3", page_icon="📡", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background-color: #050505; font-family: 'JetBrains Mono', monospace; }
    h1, h2, h3, p, span, div { color: #00ff41 !important; text-shadow: 0 0 5px #00ff41; }
    .stButton>button {
        background: transparent; color: #00ff41; border: 1px solid #00ff41;
        font-family: 'JetBrains Mono', monospace; text-transform: uppercase; letter-spacing: 2px;
    }
    .stButton>button:hover { background: #00ff41; color: #000; box-shadow: 0 0 20px #00ff41; }
    .intel-box {
        background: #001a00; border-left: 4px solid #00ff41; padding: 15px;
        margin: 10px 0; color: #d1ffd1; line-height: 1.6;
    }
    .stTextInput input { background: #000 !important; color: #00ff41 !important; border: 1px solid #00ff41 !important; }
    </style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#               SMART REQUEST (Paywall + Bot Bypass)
# ────────────────────────────────────────────────
def get_headers():
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0",
    ]
    return {"User-Agent": random.choice(agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": "https://www.google.com/"}

def smart_get(url):
    time.sleep(random.uniform(1.2, 3.8))
    headers = get_headers()

    # Try archive & 12ft first (paywall bypass)
    for prefix in ["https://archive.is/", "https://12ft.io/"]:
        try:
            r = requests.get(prefix + url, headers=headers, timeout=10, allow_redirects=True)
            if r.ok and len(r.text) > 800:
                return r
        except:
            pass

    # Direct request fallback
    try:
        r = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        if r.ok:
            return r
    except:
        pass
    return None

# ────────────────────────────────────────────────
#               AI HELPERS
# ────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def ai_summarize(text: str) -> str:
    if "HF_TOKEN" not in st.secrets:
        return "HF_TOKEN missing in secrets"
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    payload = {"inputs": text[:1100], "parameters": {"max_length": 160, "min_length": 60}}
    try:
        r = requests.post("https://api-inference.huggingface.co/models/facebook/bart-large-cnn",
                          headers=headers, json=payload, timeout=15)
        return r.json()[0]["summary_text"]
    except:
        return "AI summary unavailable"

@st.cache_data(ttl=1800)
def ai_topic(title: str) -> str:
    return ai_summarize(f"Extract key soccer elements (players, teams, action) in max 10 words: {title}")

# ────────────────────────────────────────────────
#               IMAGE SEARCH (AI topic + 3 images)
# ────────────────────────────────────────────────
@st.cache_data(ttl=1800)
def get_web_images(title: str):
    topic = ai_topic(title)
    q = f'"{title}" {topic} soccer football (match OR goal OR action OR player OR celebration) (photo OR picture OR image) -stock -shutterstock -getty -istock -meme -cartoon'
    try:
        with DDGS() as ddgs:
            res = list(ddgs.images(q, max_results=12, safesearch="off"))
        urls = []
        seen = set()
        for r in res:
            img = r.get("image")
            if img and img.startswith("http") and img not in seen:
                if any(bad in img.lower() for bad in ["stock", "shutterstock", "getty", "istock", "meme"]):
                    continue
                seen.add(img)
                urls.append(img)
                if len(urls) >= 3:
                    break
        return urls[:3]
    except:
        return []

# ────────────────────────────────────────────────
#               ARTICLE SCRAPE
# ────────────────────────────────────────────────
@st.cache_data(ttl=1800)
def scrape_article(url):
    r = smart_get(url)
    if not r:
        return "", []
    soup = BeautifulSoup(r.content, "html.parser")

    # Text
    paras = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 50]
    text = " ".join(paras[:6])

    # Images
    imgs = []
    for prop in ["og:image", "twitter:image"]:
        m = soup.find("meta", property=prop)
        if m and (val := m.get("content")) and val.startswith("http"):
            if val not in imgs:
                imgs.append(val)
    for img in soup.find_all("img", src=True):
        src = img["src"]
        if src.startswith("//"): src = "https:" + src
        src = urljoin(url, src)
        if src not in imgs and len(imgs) < 3 and not any(b in src.lower() for b in ["logo", "icon", "avatar", "gif"]):
            imgs.append(src)
    return text, imgs[:3]

# ────────────────────────────────────────────────
#               RSS FEED
# ────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_live_stream():
    feeds = [
        ("GOAL", "https://www.goal.com/en/feeds/news"),
        ("SKY", "https://www.skysports.com/rss/12040"),
        ("BBC", "https://feeds.bbci.co.uk/sport/football/rss.xml"),
        ("GUARDIAN", "https://www.theguardian.com/football/rss"),
        ("ESPN", "https://www.espn.com/espn/rss/news"),
        ("NEWS24", "https://feeds.24.com/articles/sport/featured/topstories/rss"),
        ("IOL", "https://iol.co.za/rss/iol/sport"),
    ]

    seen = {}
    for name, url in feeds:
        try:
            f = feedparser.parse(url)
            for e in f.entries:
                title = e.title.strip()
                if not title or not any(k in title.lower() for k in ["football","soccer","league","cup","goal","transfer"]):
                    continue
                link = e.link
                if link in seen:
                    continue

                thumb = None
                # media_content
                if media := e.get("media_content"):
                    for m in media:
                        if m.get("url") and m.get("type", "").startswith("image"):
                            thumb = m["url"]
                            break
                # media_thumbnail fallback
                if not thumb:
                    media_thumbs = e.get("media_thumbnail")
                    if media_thumbs:
                        thumb = media_thumbs[0].get("url")
                # enclosure
                if not thumb and e.get("enclosure"):
                    if e.enclosure.get("type", "").startswith("image"):
                        thumb = e.enclosure.get("url")

                item = {
                    "id": hashlib.md5(link.encode()).hexdigest(),
                    "title": title.upper(),
                    "link": link,
                    "source": name,
                    "thumb": thumb
                }
                seen[link] = item
        except:
            continue

    return list(seen.values())[:60]

# ────────────────────────────────────────────────
#               VIDEO
# ────────────────────────────────────────────────
def find_video(url):
    r = smart_get(url)
    if not r:
        return None, None
    soup = BeautifulSoup(r.text, "html.parser")
    for p in ["og:video", "og:video:secure_url"]:
        tag = soup.find("meta", property=p)
        if tag and tag.get("content"):
            v = tag["content"]
            return v, "youtube" if "youtube" in v else "direct"
    iframe = soup.find("iframe", src=lambda x: x and ("youtube" in x or "youtu.be" in x))
    if iframe and iframe.get("src"):
        return iframe["src"], "youtube"
    return None, None

def get_youtube_id(u):
    if "embed/" in u: return u.split("embed/")[-1].split("?")[0]
    if "watch?v=" in u: return u.split("watch?v=")[-1].split("&")[0]
    if "youtu.be/" in u: return u.split("youtu.be/")[-1].split("?")[0]
    return None

# ────────────────────────────────────────────────
#               MAIN APP
# ────────────────────────────────────────────────
st.title("📡 NEO-SCOUT // INTEL_AGGREGATOR v7.3")
st.markdown("**SOCCER • AI TOPIC UNDERSTANDING • PAYWALL BYPASS • 3 RELEVANT IMAGES**")

if st.button("🔄 REFRESH FEED"):
    get_live_stream.clear()
    st.rerun()

search = st.text_input(">> FILTER:", "").upper()
data = get_live_stream()
if search:
    data = [i for i in data if search in i["title"]]

for item in data:
    with st.container(border=True):
        st.write(f"SOURCE: **{item['source']}**")
        if item.get("thumb"):
            st.image(item["thumb"], use_container_width=True, caption="THUMB")

        st.subheader(item["title"])

        c1, c2 = st.columns([1, 4])
        with c1:
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("RUN_DEEP_INTEL", key=f"intel_{item['id']}"):
                    with st.spinner("Scraping + AI topic analysis + images..."):
                        raw, orig_imgs = scrape_article(item["link"])
                        web_imgs = get_web_images(item["title"])

                        if orig_imgs:
                            st.write("**📸 ORIGINAL SOURCE**")
                            cols = st.columns(3)
                            for i, u in enumerate(orig_imgs):
                                with cols[i]:
                                    st.image(u, use_container_width=True)
                                    st.markdown(f"[↓]({u})")

                        if web_imgs:
                            st.write("**🌐 AI-RECOMMENDED WEB IMAGES** (story + 2 more)")
                            cols = st.columns(3)
                            for i, u in enumerate(web_imgs):
                                with cols[i]:
                                    st.image(u, use_container_width=True)
                                    st.markdown(f"[↓]({u})")
                        else:
                            st.info("No additional images found")

                        if len(raw) > 150:
                            summary = ai_summarize(raw)
                            st.markdown(f"""
                                <div class="intel-box">
                                    <strong>AI SUMMARY</strong><br><br>{summary}
                                </div>
                            """, unsafe_allow_html=True)

            with col_btn2:
                if st.button("🎥 VIDEO", key=f"vid_{item['id']}"):
                    with st.spinner("Scanning video..."):
                        vurl, vtype = find_video(item["link"])
                        if vurl:
                            if vtype == "youtube":
                                yid = get_youtube_id(vurl)
                                if yid:
                                    components.html(f'<iframe width="100%" height="360" src="https://www.youtube.com/embed/{yid}" frameborder="0" allowfullscreen></iframe>', height=380)
                            else:
                                st.video(vurl)

        with c2:
            st.markdown(f"[FULL ARTICLE →]({item['link']})")

st.caption("v7.3 • Archive/12ft paywall bypass • AI topic + 3 images • Fully fixed & ready")
