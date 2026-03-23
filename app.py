import streamlit as st
import requests
import feedparser
import hashlib
import random
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import streamlit.components.v1 as components

# ────────────────────────────────────────────────
#               CYBERPUNK v8 DESIGN
# ────────────────────────────────────────────────
st.set_page_config(page_title="NEO-SCOUT • v8", page_icon="⚡️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Roboto+Mono:wght@400;500&display=swap');

:root {
    --bg: #0d0015;
    --card: rgba(20, 10, 40, 0.85);
    --cyan: #00f0ff;
    --purple: #c300ff;
}

.stApp {
    background: linear-gradient(135deg, #0d0015, #1a0033);
    color: #e0e0ff;
    font-family: 'Roboto Mono', monospace;
}

h1, h2, h3 {
    font-family: 'Orbitron', sans-serif;
    background: linear-gradient(90deg, #00f0ff, #c300ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.stButton > button {
    background: transparent;
    border: 2px solid #00f0ff;
    color: #00f0ff;
    padding: 0.8rem 1.8rem;
    border-radius: 12px;
    font-weight: 600;
}

.stButton > button:hover {
    background: linear-gradient(45deg, #00f0ff, #c300ff);
    color: #000;
    box-shadow: 0 0 25px #00f0ff;
}

.card {
    background: var(--card);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(0, 240, 255, 0.3);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}

.intel-box {
    background: rgba(25, 10, 45, 0.9);
    border-left: 5px solid #c300ff;
    padding: 1.2rem;
    border-radius: 10px;
}

.glow { text-shadow: 0 0 15px #00f0ff; }
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#               HELPERS
# ────────────────────────────────────────────────
def get_headers():
    return {"User-Agent": random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    ])}

def smart_get(url):
    time.sleep(random.uniform(0.9, 2.5))
    headers = get_headers()
    for prefix in ["https://archive.is/", "https://12ft.io/"]:
        try:
            r = requests.get(prefix + url, headers=headers, timeout=10)
            if r.ok and len(r.text) > 600:
                return r
        except:
            pass
    try:
        return requests.get(url, headers=headers, timeout=10)
    except:
        return None

# ────────────────────────────────────────────────
#               FIXED AI SUMMARY
# ────────────────────────────────────────────────
@st.cache_data(ttl=1800)
def ai_summarize(text: str) -> str:
    if "HF_TOKEN" not in st.secrets:
        return "❌ Add HF_TOKEN in secrets"
    
    try:
        r = requests.post(
            "https://api-inference.huggingface.co/models/google/flan-t5-base",
            headers={"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"},
            json={"inputs": f"summarize: {text[:950]}"},
            timeout=12
        )
        if r.ok:
            return r.json()[0]["summary_text"]
        return "HF returned error"
    except Exception as e:
        return f"Summary unavailable ({str(e)[:60]})"

# ────────────────────────────────────────────────
#               SCRAPE (only original images)
# ────────────────────────────────────────────────
@st.cache_data(ttl=1800)
def scrape_article(url):
    r = smart_get(url)
    if not r:
        return "", []

    soup = BeautifulSoup(r.content, "html.parser")
    text = " ".join([p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 45][:7])

    images = []
    for prop in ["og:image", "twitter:image"]:
        m = soup.find("meta", property=prop)
        if m and (v := m.get("content")) and v.startswith("http"):
            images.append(v)

    for img in soup.find_all("img", src=True):
        src = img["src"]
        if src.startswith("//"): src = "https:" + src
        src = urljoin(url, src)
        if src not in images and len(images) < 3 and not any(b in src.lower() for b in ["logo","icon","avatar","gif"]):
            images.append(src)

    return text, images[:3]

# ────────────────────────────────────────────────
#               FEED (fixed thumbnail logic)
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
                if not title or "football" not in title.lower() and "soccer" not in title.lower():
                    continue
                link = e.link
                if link in seen: continue
                seen.add(link)

                thumb = None
                # media_content
                if media := e.get("media_content"):
                    for m in media:
                        if m.get("url") and m.get("type", "").startswith("image"):
                            thumb = m["url"]
                            break
                # media_thumbnail (fixed - no walrus)
                if not thumb:
                    media_thumbs = e.get("media_thumbnail")
                    if media_thumbs:
                        thumb = media_thumbs[0].get("url")

                items.append({
                    "title": title.upper(),
                    "link": link,
                    "source": name,
                    "thumb": thumb,
                    "id": hashlib.md5(link.encode()).hexdigest()
                })
        except:
            continue
    return items[:60]

# ────────────────────────────────────────────────
#               MAIN
# ────────────────────────────────────────────────
st.title("⚡️ NEO-SCOUT • v8 • CYBERPUNK")
st.caption("Pure original images • Fixed neural core • New dark neon design")

if st.button("⟲ REFRESH"):
    get_soccer_feed.clear()
    st.rerun()

filter_text = st.text_input("FILTER", "").upper()

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
            if st.button("ANALYZE", key=entry["id"]):
                with st.spinner("Extracting..."):
                    text, imgs = scrape_article(entry["link"])

                    if imgs:
                        st.markdown("**📸 Original Images**")
                        cols = st.columns(len(imgs))
                        for i, img in enumerate(imgs):
                            with cols[i]:
                                st.image(img, use_container_width=True)
                                st.markdown(f"[↓]({img})")

                    summary = ai_summarize(text)
                    st.markdown(f"""
                    <div class="intel-box">
                        <strong>NEURAL CORE</strong><br><br>
                        {summary}
                    </div>
                    """, unsafe_allow_html=True)

        with c2:
            if entry.get("thumb"):
                st.image(entry["thumb"], use_container_width=True)
            st.markdown(f"[🌐 FULL REPORT]({entry['link']})")

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")

st.caption("v8 • Cyberpunk theme • Original images only • Fixed AI summary • No walrus operator")
