import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import openai
import hashlib

# ================= CONFIG =================
openai.api_key = st.secrets.get("OPENAI_API_KEY", "")

MAX_ARTICLES = 10

SOURCES = [
    "https://feeds.bbci.co.uk/sport/football/rss.xml",
    "https://www.goal.com/en/feeds/news",
    "https://www.espn.com/espn/rss/soccer/news",
    "https://www.skysports.com/rss/12040",
    "https://www.theguardian.com/football/rss",
]

# ================= FUNCTIONS =================

def get_article_content(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text() for p in paragraphs])
        return text[:5000]
    except:
        return None


def summarize_article(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": f"Summarize this football article into a short engaging Facebook post:\n{text}"}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"


def fetch_news():
    articles = []
    seen = set()

    for source in SOURCES:
        feed = feedparser.parse(source)
        for entry in feed.entries[:MAX_ARTICLES]:
            article_id = hashlib.md5(entry.link.encode()).hexdigest()
            if article_id in seen:
                continue

            content = get_article_content(entry.link)
            if not content:
                continue

            summary = summarize_article(content)

            articles.append({
                "title": entry.title,
                "summary": summary,
                "link": entry.link
            })

            seen.add(article_id)

    return articles

# ================= STREAMLIT UI =================

st.set_page_config(page_title="⚽ AI Football News", layout="wide")

st.title("⚽ AI Football News Scraper")
st.write("Latest football news automatically summarized for social media.")

if st.button("🔄 Fetch Latest News"):
    with st.spinner("Fetching & summarizing..."):
        news = fetch_news()

    for article in news:
        st.subheader(article["title"])
        st.write(article["summary"])
        st.markdown(f"[Read full article]({article['link']})")
        st.divider()
