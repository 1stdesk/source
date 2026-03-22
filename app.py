import streamlit as st
import requests
import feedparser
import hashlib
from bs4 import BeautifulSoup
import random

# --- CONFIG ---
st.set_page_config(page_title="NEO-SCOUT V13", page_icon="📡", layout="wide")

# --- SESSION ---
if "refresh_key" not in st.session_state:
    st.session_state.refresh_key = 0

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ NEO-SCOUT")

    if st.button("🔄 Refresh Feed"):
        st.session_state.refresh_key += 1
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")

    st.subheader("Filters")
    show_breaking = st.checkbox("🚨 Breaking Only")
    show_images = st.checkbox("🖼 Show Images", value=True)

# --- CLEAN TEXT ---
def clean_text(text):
    lines = text.split("\n")
    cleaned, seen = [], set()

    for line in lines:
        line = line.strip()
        if len(line) < 40:
            continue
        if any(x in line.lower() for x in ["cookie", "subscribe", "sign up"]):
            continue
        if line not in seen:
            seen.add(line)
            cleaned.append(line)

    return " ".join(cleaned)

def clean_summary(summary):
    sentences = summary.split(". ")
    unique, seen = [], set()

    for s in sentences:
        s = s.strip()
        if s and s not in seen:
            seen.add(s)
            unique.append(s)

    return ". ".join(unique[:3]).strip() + "."

# --- SIMILARITY ---
def is_similar(t1, t2):
    ignore = {"the","and","to","in","of","for","on","with"}
    s1 = set([w for w in t1.lower().split() if w not in ignore])
    s2 = set([w for w in t2.lower().split() if w not in ignore])
    return len(s1.intersection(s2)) >= 3

def find_related(main, all_items):
    return [i for i in all_items if i["id"] != main["id"] and is_similar(main["title"], i["title"])][:5]

# --- SCRAPER ---
def scrape_intel(url):
    try:
        r = requests.get(url, timeout=6, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.content, 'html.parser')

        img = soup.find("meta", property="og:image")

        paras = [p.get_text().strip() for p in soup.find_all('p')]
        paras = [p for p in paras if len(p) > 60]

        text = clean_text(" ".join(paras[:6]))

        return text, (img["content"] if img else None)

    except:
        return "", None

# --- MERGE ---
def merge_articles(main, all_items):
    related = find_related(main, all_items)

    combined = ""
    main_text, img = scrape_intel(main["link"])
    combined += main_text

    for r in related:
        txt, _ = scrape_intel(r["link"])
        combined += "\n" + txt

    return combined, related, img

# --- AI ---
def smart_fallback(text):
    s = text.split(". ")
    return ". ".join(s[:3]) if len(s) >= 3 else text[:200]

def query_ai(text, title=""):
    if "HF_TOKEN" not in st.secrets:
        return clean_summary(smart_fallback(text))

    API = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
    headers = {"Authorization": f"Bearer {st.secrets['HF_TOKEN']}"}

    prompt = f"""
Write a professional football news summary.

Max 60 words. No repetition.

Title: {title}

{text[:1200]}
"""

    try:
        r = requests.post(API, headers=headers, json={"inputs": prompt}, timeout=20)
        res = r.json()

        if isinstance(res, list):
            return clean_summary(res[0]["summary_text"])
    except:
        pass

    return clean_summary(smart_fallback(text))

@st.cache_data(ttl=3600)
def cached_summary(text, title):
    return query_ai(text, title)

# --- TAGS ---
def generate_tags(title):
    base = ["#Football", "#SoccerNews", "#Breaking"]
    if "transfer" in title.lower():
        base += ["#Transfer"]
    return " ".join(random.sample(base, k=min(4, len(base))))

# --- BREAKING ---
def is_breaking(title):
    return any(k in title for k in ["BREAKING", "CONFIRMED"])

# --- FEEDS ---
@st.cache_data(ttl=600)
def get_news(key):
    feeds = [
        "https://www.goal.com/en/feeds/news",
        "https://www.skysports.com/rss/12040",
        "http://feeds.bbci.co.uk/sport/football/rss.xml",
        "https://www.espn.com/espn/rss/soccer/news",
        "https://www.theguardian.com/football/rss"
    ]

    out = []
    for url in feeds:
        f = feedparser.parse(url)
        for e in f.entries[:3]:
            out.append({
                "id": hashlib.md5(e.link.encode()).hexdigest(),
                "title": e.title.upper(),
                "link": e.link,
                "src": url.split('/')[2]
            })
    return out

# --- HEADER ---
st.title("📡 NEO-SCOUT V13")
st.caption("Real-Time Football Intelligence Terminal")

# --- STYLES ---
st.markdown("""
<style>
.news-card {
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 14px;
    margin-bottom: 12px;
    background: #ffffff;
}

.news-title {
    font-size: 17px;
    font-weight: 600;
}

.news-source {
    font-size: 12px;
    color: #6b7280;
}

.breaking {
    color: red;
    font-size: 12px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# --- MAIN ---
news = get_news(st.session_state.refresh_key)

for item in news:

    if show_breaking and not is_breaking(item["title"]):
        continue

    st.markdown('<div class="news-card">', unsafe_allow_html=True)

    st.markdown(f"<div class='news-source'>{item['src']}</div>", unsafe_allow_html=True)

    if is_breaking(item["title"]):
        st.markdown("<div class='breaking'>🚨 BREAKING</div>", unsafe_allow_html=True)

    st.markdown(f"<div class='news-title'>{item['title']}</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1,2])

    with col1:
        if st.button("Analyze", key=item["id"]):

            with st.spinner("Processing..."):

                merged_text, related, img = merge_articles(item, news)

                if img and show_images:
                    st.image(img)

                summary = cached_summary(merged_text, item["title"])
                tags = generate_tags(item["title"])

                st.write(summary)
                st.caption(tags)

    with col2:
        with st.expander("Sources"):
            merged_text, related, _ = merge_articles(item, news)
            for r in related:
                st.write(f"- {r['src']}")

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.write("SYSTEM ACTIVE // V13 TERMINAL")
