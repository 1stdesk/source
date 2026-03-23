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
#               NEW 2026 CYBERPUNK DESIGN
# ────────────────────────────────────────────────
st.set_page_config(page_title="NEO-SCOUT • v8", page_icon="⚡️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Roboto+Mono:wght@400;500&display=swap');

:root {
    --bg: #0d0015;
    --card: rgba(18, 10, 35, 0.78);
    --neon-cyan: #00f0ff;
    --neon-purple: #c300ff;
    --text: #e0e0ff;
    --text-dim: #a0a0cc;
    --glow: 0 0 18px rgba(0, 240, 255, 0.6);
    --glow-purple: 0 0 20px rgba(195, 0, 255, 0.55);
}

.stApp {
    background: var(--bg);
    color: var(--text);
    font-family: 'Roboto Mono', monospace;
}

h1, h2, h3 {
    font-family: 'Orbitron', sans-serif;
    background: linear-gradient(90deg, var(--neon-cyan), var(--neon-purple));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: var(--glow);
}

.stButton > button {
    background: transparent;
    border: 1.5px solid var(--neon-cyan);
    color: var(--neon-cyan);
    font-weight: 500;
    padding: 0.7rem 1.6rem;
    border-radius: 8px;
    transition: all 0.35s ease;
    text-shadow: 0 0 8px var(--neon-cyan);
}

.stButton > button:hover {
    background: linear-gradient(45deg, var(--neon-cyan), var(--neon-purple));
    color: #000;
    box-shadow: var(--glow), var(--glow-purple);
    transform: translateY(-2px);
}

.card {
    background: var(--card);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(0, 240, 255, 0.22);
    border-radius: 14px;
    padding: 1.6rem;
    margin-bottom: 1.4rem;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6), inset 0 0 12px rgba(0, 240, 255, 0.08);
    transition: all 0.4s ease;
}

.card:hover {
    transform: translateY(-6px);
    box-shadow: 0 16px 48px rgba(0, 240, 255, 0.25), inset 0 0 20px rgba(195, 0, 255, 0.12);
}

.intel-box {
    background: rgba(15, 5, 35, 0.85);
    border-left: 5px solid var(--neon-purple);
    padding: 1.2rem 1.5rem;
    border-radius: 10px;
    margin: 1rem 0;
    box-shadow: inset 0 0 15px rgba(195, 0, 255, 0.18);
}

.glow-text {
    text-shadow: 0 0 12px var(--neon-cyan), 0 0 24px var(--neon-purple);
}

.stTextInput input {
    background: rgba(20, 10, 40, 0.9) !important;
    color: var(--text) !important;
    border: 1px solid rgba(0, 240, 255, 0.4) !important;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ────────────────────────────────────────────────
#               REQUEST HELPERS
# ────────────────────────────────────────────────
def get_headers():
    agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0",
    ]
    return {"User-Agent": random.choice(agents)}

def smart_get(url, timeout=10):
    time.sleep(random.uniform(0.9, 2.8))
    headers = get_headers()

    # Paywall bypass
    for prefix in ["https://archive.is/", "https://12ft.io/"]:
        try:
            r = requests.get(prefix + url, headers=headers, timeout=timeout)
            if r.ok and len(r.text) > 600:
                return r
        except:
            pass

    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.ok:
            return r
    except:
        pass
    return None

# ────────────────────────────────────────────────
#               AI SUMMARY – FIXED & MORE RELIABLE
# ────────────────────────────────────────────────
@st.cache_data(ttl=1800)
def ai_summarize(text: str) -> str:
    if "HF_TOKEN" not in st.secrets:
        return "HF_TOKEN missing in secrets.toml"

    # Using flan-t5-base → faster & more available than bart-large-cnn
    url = "https://api-inference.huggingface.co/models/google/flan-t5-base"
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}

    payload = {
        "inputs": f"summarize: {text[:950]}",
        "parameters": {
            "max_length": 140,
            "min_length": 50,
            "do_sample": False
        }
    }

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=12)
        if r.status_code == 200:
            result = r.json()
            if isinstance(result, list) and result:
                return result[0].get("summary_text", "—").strip()
        return f"HF returned {r.status_code}"
    except requests.exceptions.Timeout:
        return "Summary timeout – article too long or server busy"
    except Exception as e:
        return f"AI connection error: {str(e)[:70]}"

# ────────────────────────────────────────────────
#               SCRAPE ARTICLE (only original images)
# ────────────────────────────────────────────────
@st.cache_data(ttl=1800)
def scrape_article(url):
    r = smart_get(url)
    if not r:
        return "", []

    soup = BeautifulSoup(r.content, "html.parser")

    # Text
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 45]
    text = " ".join(paragraphs[:7])

    # Only original images (no web/AI search)
    images = []
    for prop in ["og:image", "og:image:secure_url", "twitter:image"]:
        meta = soup.find("meta", property=prop)
        if meta and (val := meta.get("content")) and val.startswith("http"):
            if val not in images:
                images.append(val)

    for img in soup.find_all("img", src=True):
        src = img["src"]
        if src.startswith("//"): src = "https:" + src
        src = urljoin(url, src)
        bad = {"logo", "icon", "banner", "avatar", "pixel", "blank", "gif"}
        if src not in images and len(images) < 3 and not any(b in src.lower() for b in bad):
            images.append(src)

    return text, images[:3]

# ────────────────────────────────────────────────
#               RSS FEED
# ────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_soccer_feed():
    sources = [
        ("Goal", "https://www.goal.com/en/feeds/news"),
        ("Sky Sports", "https://www.skysports.com/rss/12040"),
        ("BBC Football", "https://feeds.bbci.co.uk/sport/football/rss.xml"),
        ("Guardian Football", "https://www.theguardian.com/football/rss"),
        ("News24 Sport", "https://feeds.24.com/articles/sport/featured/topstories/rss"),
    ]

    items = []
    seen = set()

    for name, url in sources:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                title = entry.title.strip()
                if not title or not any(k in title.lower() for k in ["football","soccer","premier","league","cup","goal","transfer"]):
                    continue
                link = entry.link
                if link in seen:
                    continue
                seen.add(link)

                thumb = None
                if media := entry.get("media_content"):
                    for m in media:
                        if m.get("url") and m.get("type","").startswith("image"):
                            thumb = m["url"]
                            break
                if not thumb and thumbs := entry.get("media_thumbnail"):
                    thumb = thumbs[0].get("url")

                items.append({
                    "title": title.upper(),
                    "link": link,
                    "source": name,
                    "thumb": thumb,
                    "id": hashlib.md5(link.encode()).hexdigest()
                })
        except:
            continue

    items.sort(key=lambda x: x.get("published_parsed", time.gmtime(0)), reverse=True)
    return items[:50]

# ────────────────────────────────────────────────
#               MAIN UI
# ────────────────────────────────────────────────
st.title("⚡️ NEO-SCOUT • v8 • CYBERPUNK FEED")
st.caption("Soccer intelligence • paywall-aware • pure original visuals • neural summaries")

if st.button("⟲ REFRESH STREAM"):
    get_soccer_feed.clear()
    st.rerun()

q = st.text_input("FILTER HEADLINES", "").upper().strip()

feed = get_soccer_feed()
if q:
    feed = [e for e in feed if q in e["title"]]

for entry in feed:
    with st.container():
        st.markdown(f'<div class="card">', unsafe_allow_html=True)

        col_left, col_right = st.columns([3,1])

        with col_left:
            st.subheader(entry["title"])
            st.caption(f"Source: {entry['source']}")

            if st.button("ANALYZE ARTICLE", key=f"deep_{entry['id']}"):
                with st.spinner("Infiltrating source..."):
                    text, imgs = scrape_article(entry["link"])

                    if imgs:
                        st.markdown("**Captured visuals**")
                        cols = st.columns(min(3, len(imgs)))
                        for i, img_url in enumerate(imgs):
                            with cols[i]:
                                st.image(img_url, use_column_width=True)
                                st.markdown(f"[↓]({img_url})")
                    else:
                        st.info("No usable images extracted")

                    summary = ai_summarize(text)
                    if "error" in summary.lower() or "missing" in summary.lower():
                        st.warning(summary)
                        if text:
                            st.markdown(f"**Quick preview:**  \n> {text[:340]}{'...' if len(text)>340 else ''}")
                    else:
                        st.markdown(f"""
                        <div class="intel-box">
                            <strong>NEURAL SUMMARY</strong><br><br>
                            {summary}
                        </div>
                        """, unsafe_allow_html=True)

        with col_right:
            if entry.get("thumb"):
                st.image(entry["thumb"], use_column_width=True)
            st.markdown(f"[→ READ]({entry['link']})")

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("<hr style='border-color:rgba(0,240,255,0.2)'>", unsafe_allow_html=True)

st.markdown("---")
st.caption("NEO-SCOUT v8 • Cyberpunk edition • 2026 • original images only • fixed neural core")
