import streamlit as st
import feedparser
import re

# ================= CONFIG =================
st.set_page_config(page_title="⚽ Football News", layout="wide")

SOURCES = [
    ("BBC", "https://feeds.bbci.co.uk/sport/football/rss.xml"),
    ("ESPN", "https://www.espn.com/espn/rss/soccer/news"),
]

MAX_ARTICLES = 5

# ================= HELPERS =================
def clean_html(text):
    return re.sub('<.*?>', '', text)

def short_summary(text):
    text = clean_html(text)
    sentences = text.split(".")
    return ". ".join(sentences[:2]) + "."

# ================= FETCH =================
@st.cache_data(ttl=300)
def fetch_news():
    all_articles = []

    for name, url in SOURCES:
        feed = feedparser.parse(url)

        for entry in feed.entries[:MAX_ARTICLES]:
            summary = entry.get("summary", "")

            image = None
            if "media_content" in entry:
                image = entry.media_content[0]["url"]

            all_articles.append({
                "source": name,
                "title": entry.title,
                "summary": short_summary(summary),
                "link": entry.link,
                "image": image
            })

    return all_articles

# ================= UI =================

# HEADER
st.markdown("""
<h1 style='text-align:center;'>⚽ Football News</h1>
<p style='text-align:center;color:gray;'>Live • Fast • Mobile</p>
""", unsafe_allow_html=True)

# LOAD
with st.spinner("Loading latest news..."):
    articles = fetch_news()

# FEATURED (top story)
if articles:
    top = articles[0]

    st.markdown("## 🔥 Top Story")
    if top["image"]:
        st.image(top["image"], use_container_width=True)

    st.markdown(f"### {top['title']}")
    st.write(top["summary"])
    st.markdown(f"[Read more →]({top['link']})")

    st.divider()

# GRID LAYOUT (BBC style)
st.markdown("## 📰 Latest News")

cols = st.columns(2)

for i, article in enumerate(articles[1:]):
    with cols[i % 2]:
        with st.container():
            if article["image"]:
                st.image(article["image"], use_container_width=True)

            st.markdown(f"**{article['title']}**")
            st.caption(article["source"])
            st.write(article["summary"])
            st.markdown(f"[Read more →]({article['link']})")

            st.markdown("---")
