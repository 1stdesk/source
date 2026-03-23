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

st.set_page_config(page_title="NEO-SCOUT v7.3", page_icon="📡", layout="wide")

# ─── Futuristic Terminal Style ───────────────────────────────────────────────
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp {
        background-color: #050505;
        font-family: 'JetBrains Mono', monospace;
        color: #00ff41;
    }
    h1, h2, h3, p, span, div, label, .stMarkdown {
        color: #00ff41 !important;
        text-shadow: 0 0 5px #00ff41;
    }
    .stButton > button {
        background: transparent;
        color: #00ff41;
        border: 1px solid #00ff41;
        font-family: 'JetBrains Mono', monospace;
        text-transform: uppercase;
        letter-spacing: 2px;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background: #00ff41;
        color: #000;
        box-shadow: 0 0 20px #00ff41;
    }
    .intel-box {
        background: #001a00;
        border-left: 4px solid #00ff41;
        padding: 16px;
        margin: 12px 0;
        font-size: 0.95rem;
        line-height: 1.6;
        color: #d1ffd1;
    }
    .stTextInput input {
        background: #000 !important;
        color: #00ff41 !important;
        border: 1px solid #00ff41 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ─── Helpers ─────────────────────────────────────────────────────────────────

def get_headers():
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0",
    ]
    return {
        "User-Agent": random.choice(agents),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
        "DNT": "1",
    }

def smart_get(url, timeout=10):
    time.sleep(random.uniform(1.1, 3.9))

    # Try archive.is / 12ft.io first (paywall bypass)
    for prefix in ["https://archive.is/", "https://12ft.io/"]:
        try:
            test_url = prefix + url
            r = requests.get(test_url, headers=get_headers(), timeout=timeout, allow_redirects=True)
            if r.ok and len(r.text) > 800:
                return r
        except:
            pass

    # Direct attempt with bot-friendly headers
    try:
        r = requests.get(url, headers=get_headers(), timeout=timeout, allow_redirects=True)
        if r.ok:
            return r
    except:
        pass

    return None

# ─── AI Helpers (using HuggingFace inference) ────────────────────────────────

@st.cache_data(ttl=3600)
def ai_summarize(text: str) -> str:
    if "HF_TOKEN" not in st.secrets:
        return "[HF_TOKEN missing in secrets]"

    url = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}
    payload = {
        "inputs": text[:1100],
        "parameters": {
            "max_length": 160,
            "min_length": 60,
            "do_sample": False,
            "repetition_penalty": 1.15
        }
    }

    for _ in range(3):
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            data = resp.json()
            if isinstance(data, list) and data:
                return data[0].get("summary_text", "— summary failed —")
            time.sleep(4)
        except:
            time.sleep(3)
    return "— summary timeout —"

@st.cache_data(ttl=1800)
def ai_extract_topic(title: str) -> str:
    prompt = f"Extract key soccer elements (teams, players, event, action) in max 10 words: {title}"
    summary = ai_summarize(prompt)
    return summary.strip() or title[:80]

# ─── Image Search ────────────────────────────────────────────────────────────

@st.cache_data(ttl=1800)
def get_relevant_images(title: str):
    topic = ai_extract_topic(title)
    query = (
        f'"{title}" {topic} '
        f'(soccer OR football) (match OR goal OR action OR celebration OR player) '
        f'(photo OR picture OR image OR shot) '
        f'-stock -shutterstock -getty -istock -alamy -cartoon -illustration -meme -ai -generated'
    )

    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=12, safesearch="off"))

        urls = []
        seen = set()
        for r in results:
            img = r.get("image")
            if not img or not img.startswith("http") or img in seen:
                continue
            low = img.lower()
            if any(x in low for x in ["stock", "shutterstock", "getty", "istock", "alamy", "meme", "cartoon"]):
                continue
            seen.add(img)
            urls.append(img)
            if len(urls) >= 3:
                break
        return urls[:3]
    except:
        return []

# ─── Article Scraping ────────────────────────────────────────────────────────

@st.cache_data(ttl=1800)
def scrape_article(url: str):
    r = smart_get(url)
    if not r:
        return "", []

    soup = BeautifulSoup(r.content, "html.parser")

    # Text
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 50]
    text = " ".join(paragraphs[:6])

    # Images (meta + content images)
    images = []
    for tag in ["og:image", "og:image:secure_url", "twitter:image"]:
        m = soup.find("meta", property=tag)
        if m and (val := m.get("content")) and val.startswith("http"):
            if val not in images:
                images.append(val)

    # Fallback to img tags
    for img in soup.find_all("img", src=True):
        src = img["src"]
        if src.startswith("//"): src = "https:" + src
        src = urljoin(url, src)
        bad = {"logo", "icon", "avatar", "banner", "pixel", "blank", "gif"}
        if src not in images and len(images) < 4 and not any(b in src.lower() for b in bad):
            images.append(src)

    return text, images[:3]

# ─── RSS Aggregation ─────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_soccer_feed():
    sources = [
        ("Goal",           "https://www.goal.com/en/feeds/news"),
        ("Sky Sports",     "https://www.skysports.com/rss/12040"),
        ("BBC Football",   "https://feeds.bbci.co.uk/sport/football/rss.xml"),
        ("Guardian Football","https://www.theguardian.com/football/rss"),
        ("ESPN",           "https://www.espn.com/espn/rss/news"),
        ("News24 Sport",   "https://feeds.24.com/articles/sport/featured/topstories/rss"),
        ("IOL Sport",      "https://iol.co.za/rss/iol/sport"),
    ]

    items = []
    seen = set()

    for name, feed_url in sources:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title = entry.get("title", "").strip()
                if not title or not is_soccer_related(title):
                    continue

                link = entry.get("link", "")
                if link in seen:
                    continue
                seen.add(link)

                thumb = None
                if media := entry.get("media_content"):
                    for m in media:
                        if m.get("type", "").startswith("image"):
                            thumb = m.get("url")
                            break
                if not thumb and media_thumbs := entry.get("media_thumbnail"):
                    thumb = media_thumbs[0].get("url")

                items.append({
                    "title": title.upper(),
                    "link": link,
                    "source": name,
                    "thumb": thumb,
                    "id": hashlib.md5(link.encode()).hexdigest(),
                    "published": entry.get("published_parsed") or entry.get("updated_parsed")
                })
        except:
            continue

    items.sort(key=lambda x: x["published"] or time.gmtime(0), reverse=True)
    return items[:60]

def is_soccer_related(title: str) -> bool:
    lower = title.lower()
    terms = [
        "football", "soccer", "premier league", "champions league", "epl", "bundesliga",
        "la liga", "serie a", "ligue 1", "world cup", "euro", "uefa", "afcon", "fifa",
        "kaizer chiefs", "orlando pirates", "mamelodi sundowns", "man city", "liverpool",
        "arsenal", "chelsea", "man united", "goal", "transfer", "match", "highlights"
    ]
    return any(t in lower for t in terms)

# ─── Video Detection ─────────────────────────────────────────────────────────

def find_video(url):
    r = smart_get(url, timeout=6)
    if not r:
        return None, None

    soup = BeautifulSoup(r.text, "html.parser")

    # Open Graph video
    for prop in ["og:video", "og:video:secure_url"]:
        tag = soup.find("meta", property=prop)
        if tag and (v := tag.get("content")):
            if "youtube" in v or "youtu.be" in v:
                return v, "youtube"
            return v, "direct"

    # YouTube embed / iframe
    iframe = soup.find("iframe", src=lambda s: s and ("youtube.com/embed" in s or "youtu.be" in s))
    if iframe and (src := iframe.get("src")):
        return src, "youtube"

    return None, None

def youtube_id_from_url(url):
    if not url:
        return None
    patterns = [
        "embed/", "watch?v=", "youtu.be/"
    ]
    for p in patterns:
        if p in url:
            part = url.split(p)[-1].split("?")[0].split("&")[0]
            return part
    return None

# ─── UI ──────────────────────────────────────────────────────────────────────

st.title("📡 NEO-SCOUT  v7.3")
st.caption("Soccer news aggregator • AI topic understanding • paywall-aware scraping • relevant web images")

if st.button("⟳ Refresh feed", type="primary"):
    load_soccer_feed.clear()
    st.rerun()

query = st.text_input("Filter headlines", "").upper().strip()

feed = load_soccer_feed()
if query:
    feed = [e for e in feed if query in e["title"]]

for entry in feed:
    with st.container(border=True):
        st.write(f"**{entry['source']}**")
        if entry["thumb"]:
            st.image(entry["thumb"], use_column_width=True)

        st.subheader(entry["title"])

        colA, colB = st.columns([1, 4])

        with colA:
            b1, b2 = st.columns(2)

            with b1:
                if st.button("Deep Intel", key=f"intel_{entry['id']}"):
                    with st.spinner("Analyzing article + searching relevant images..."):
                        text, orig_imgs = scrape_article(entry["link"])

                        web_imgs = get_relevant_images(entry["title"])

                        # Original images
                        if orig_imgs:
                            st.markdown("**Original article images**")
                            cols = st.columns(min(3, len(orig_imgs)))
                            for i, img in enumerate(orig_imgs):
                                with cols[i % 3]:
                                    try:
                                        st.image(img, use_column_width=True)
                                    except:
                                        st.caption("Image unavailable")
                                    st.markdown(f"[⬇]({img})")

                        # AI-guided web images
                        if web_imgs:
                            st.markdown("**AI-relevant web images**")
                            cols = st.columns(min(3, len(web_imgs)))
                            for i, img in enumerate(web_imgs):
                                with cols[i % 3]:
                                    try:
                                        st.image(img, use_column_width=True)
                                    except:
                                        st.caption("Image unavailable")
                                    st.markdown(f"[⬇]({img})")
                        else:
                            st.info("No good matching images found")

                        # Summary
                        if len(text) > 180:
                            summary = ai_summarize(text)
                            st.markdown(f"""
                            <div class="intel-box">
                                <strong>AI Summary</strong><br><br>
                                {summary}
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.info("Article text too short to summarize")

            with b2:
                if st.button("Find Video", key=f"vid_{entry['id']}"):
                    with st.spinner("Looking for embedded video..."):
                        vid_url, vtype = find_video(entry["link"])
                        if vid_url:
                            if vtype == "youtube":
                                yid = youtube_id_from_url(vid_url)
                                if yid:
                                    components.html(
                                        f'<iframe width="100%" height="360" '
                                        f'src="https://www.youtube.com/embed/{yid}" '
                                        f'frameborder="0" allowfullscreen></iframe>',
                                        height=380
                                    )
                            else:
                                st.video(vid_url)
                        else:
                            st.info("No video found on page")

        with colB:
            st.markdown(f"[Read full article →]({entry['link']})")

st.markdown("---")
st.caption("NEO-SCOUT v7.3  •  AI topic understanding • archive/12ft bypass • DuckDuckGo image search")
