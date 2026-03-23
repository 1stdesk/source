import streamlit as st
import requests
import feedparser
import hashlib
import random
import time
from duckduckgo_search import DDGS

# ────────────────────────────────────────────────
#               CYBERPUNK DESIGN v8.2
# ────────────────────────────────────────────────
st.set_page_config(page_title="NEO-SCOUT • v8.2", page_icon="⚡️", layout="wide")

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

@st.cache_data(ttl=1800)
def ai_topic(title):
    # Keeping Flan-T5 here because BART is strictly for summaries, not instruction-following.
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

# ────── NEW: FIRECRAWL SCRAPER ──────
@st.cache_data(ttl=1800)
def scrape_article(url):
    if "FIRECRAWL_KEY" not in st.secrets:
        return "🔒 Missing FIRECRAWL_KEY in secrets.toml", [], None
        
    headers = {
        "Authorization": f"Bearer {st.secrets['FIRECRAWL_KEY']}",
        "Content-Type": "application/json"
    }
    payload = {
        "url": url,
        "formats": ["markdown"]
    }
    
    try:
        r = requests.post("https://api.firecrawl.dev/v1/scrape", json=payload, headers=headers, timeout=30)
        if r.ok:
            data = r.json().get("data", {})
            text = data.get("markdown", "")
            meta = data.get("metadata", {})
            
            # Firecrawl easily pulls the meta images for us
            head_img = meta.get("og:image") or meta.get("twitter:image")
            
            return text, [head_img] if head_img else [], head_img
        else:
            return f"⚠️ Firecrawl Error: {r.status_code} - {r.text}", [], None
    except Exception as e:
        return f"Error: {str(e)}", [], None

# ────── NEW: FACEBOOK BART SUMMARY ──────
@st.cache_data(ttl=1800)
def ai_summarize(text: str) -> str:
    if len(text.strip()) < 50:
        return "📭 Not enough text extracted from the article."
    if "HF_TOKEN" not in st.secrets:
        return "🔒 Add `HF_TOKEN` to your secrets.toml for full cyberpunk AI summary.\n\n" + text[:450] + "..."
    try:
        # BART doesn't need a prompt, just the raw markdown/text
        r = requests.post(
            "https://api-inference.huggingface.co/models/facebook/bart-large-cnn",
            headers={"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"},
            json={
                "inputs": text[:3500], # ~800 tokens, safe limit for BART
                "parameters": {
                    "max_length": 130, 
                    "min_length": 40,
                    "do_sample": False
                }
            }
        )
        if r.ok:
            res = r.json()
            if isinstance(res, list) and len(res) > 0:
                return res[0].get("summary_text", "Summary ready ⚡️")
            return str(res)
        else:
            return f"⚠️ HF API {r.status_code} — still shows raw text below:\n\n{text[:500]}..."
    except Exception as e:
        return f"🛠️ Neural core offline ({str(e)[:80]})\n\nFallback: {text[:400]}..."

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
st.title("⚡️ NEO-SCOUT • v8.2 • CYBERPUNK")
st.caption("✅ Firecrawl Data Extraction + Facebook BART Neural Summary")

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
            if st.button("🚀 ANALYZE ARTICLE", key=f"btn_{entry['id']}"):
                with st.spinner("🧠 Extracting via Firecrawl + processing BART summary..."):
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

                    # 🔥 AI Summary — NOW POWERED BY BART
                    summary = ai_summarize(text)
                    st.markdown(f"""
                    <div class="intel-box">
                        <strong>🧬 BART NEURAL SUMMARY</strong><br><br>
                        {summary}
                    </div>
                    """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"[→ FULL STORY]({entry['link']})")

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")

st.caption("v8.2 • Powered by Firecrawl & Facebook BART • Enjoy the neon!")
