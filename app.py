import streamlit as st
import requests
import feedparser
import re
import os
import hashlib
from collections import Counter
from bs4 import BeautifulSoup
from datetime import datetime, timedelta, timezone
import nltk

# ────────────────────────────────────────────────
# NLTK FIX (For Cloud Deployment)
# ────────────────────────────────────────────────
NLTK_DIR = "/tmp/nltk_data"
os.makedirs(NLTK_DIR, exist_ok=True)
nltk.data.path.append(NLTK_DIR)

try:
    nltk.download("punkt", download_dir=NLTK_DIR)
    nltk.download("stopwords", download_dir=NLTK_DIR)
except:
    pass

# ────────────────────────────────────────────────
# CONFIG
# ────────────────────────────────────────────────
st.set_page_config(page_title="NEO-SCOUT v17.5", page_icon="⚽", layout="wide")

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

# ────────────────────────────────────────────────
# 🌍 COMPLETE 100+ SOURCE LIST
# ────────────────────────────────────────────────
ALL_SOURCES = [
    # --- GLOBAL & EUROPEAN GIANTS ---
    ("GOAL", "https://www.goal.com/en/feeds/news"),
    ("BBC", "https://feeds.bbci.co.uk/sport/football/rss.xml"),
    ("GUARDIAN", "https://www.theguardian.com/football/rss"),
    ("ESPN", "https://www.espn.com/espn/rss/soccer/news"),
    ("SKY", "https://www.skysports.com/rss/12040"),
    ("90MIN", "https://www.90min.com/posts.rss"),
    ("CBS", "https://www.cbssports.com/rss/headlines/soccer/"),
    ("NBC", "https://www.nbcsports.com/soccer/rss.xml"),
    ("YAHOO", "https://sports.yahoo.com/soccer/rss/"),
    ("FOX", "https://api.foxsports.com/v1/rss?category=soccer"),
    ("REUTERS", "https://www.reutersagency.com/feed/?best-topics=sports"),
    ("AP", "https://apnews.com/hub/soccer"),
    ("MIRROR", "https://www.mirror.co.uk/sport/football/rss.xml"),
    ("INDEPENDENT", "https://www.independent.co.uk/sport/football/rss"),
    ("STANDARD", "https://www.standard.co.uk/sport/football/rss"),
    ("TALKSport", "https://talksport.com/football/feed/"),
    ("GIVEMESPORT", "https://www.givemesport.com/feed/"),
    ("FOOTBALL365", "https://www.football365.com/rss"),
    ("BLEACHER", "https://bleacherreport.com/articles.rss"),
    ("ATHLETIC", "https://theathletic.com/rss/football/"),
    ("FOURFOURTWO", "https://www.fourfourtwo.com/rss.xml"),
    ("CAUGHTOFFSIDE", "https://www.caughtoffside.com/feed/"),
    ("TEAMTALK", "https://www.teamtalk.com/feed"),
    ("WORLD SOCCER TALK", "https://worldsoccertalk.com/feed/"),
    ("SOCCERLENS", "https://soccerlens.com/feed/"),
    ("TRIBAL FOOTBALL", "https://www.tribalfootball.com/rss.xml"),
    ("101 GREAT GOALS", "https://www.101greatgoals.com/feed/"),
    ("SOCCER NEWS", "https://www.soccernews.com/feed/"),
    ("TRANSFERMARKT", "https://www.transfermarkt.com/rss/news"),
    ("INSIDE WORLD FOOTBALL", "https://www.insideworldfootball.com/feed/"),
    ("AS ENGLISH", "https://en.as.com/rss/en/soccer.xml"),
    ("MARCA ENGLISH", "https://e00-marca.uecdn.es/rss/en/index.xml"),
    ("FOOTBALL ITALIA", "https://football-italia.net/feed/"),
    ("WHOSCORED", "https://www.whoscored.com/Articles/Feed"),
    ("EUROSPORT", "https://www.eurosport.com/football/rss.xml"),
    ("SOCCER AM", "https://www.socceram.com/rss/12040"),
    ("FOOTBALL ORANJE", "http://www.football-oranje.com/feed/"),
    ("SBNATION SOCCER", "https://www.sbnation.com/soccer/rss/current"),
    ("BEIN SPORTS", "https://www.beinsports.com/en/rss/soccer"),
    ("COPA90", "https://copa90.com/feed/"),

    # --- AFRICA: PAN-AFRICAN & REGIONAL ---
    ("SUPERSPORT", "https://supersport.com/rss/football"),
    ("KICKOFF", "https://www.kickoff.com/news/rss"),
    ("AFRICAN FOOTBALL", "https://africanfootball.com/news/rss"),
    ("KINGFUT", "https://www.kingfut.com/feed/"),
    ("SOCCER LADUMA", "https://www.snl24.com/soccerladuma/feed"),
    ("SOKA25EAST", "https://soka25east.com/feed/"),
    ("AFRIK-FOOT", "https://www.afrik-foot.com/feed"),
    ("ALL AFRICA SOCCER", "https://allafrica.com/tools/headlines/rdf/soccer/headlines.rdf"),
    ("FARPOST", "https://farpost.co.za/feed/"),
    ("SPORT NEWS AFRICA", "https://sportnewsafrica.com/en/feed/"),
    ("KAOWO FOOT", "https://www.kawowo.com/feed/"),
    ("FOOTY GHANA", "https://footy-ghana.com/feed/"),
    ("CITI SPORTS", "https://citisportsonline.com/feed/"),
    ("PULSE SPORTS", "https://www.pulsesports.ng/rss"),
    ("GHANA SOCCERNET", "https://ghanasoccernet.com/feed"),
    ("NIGERIA SOCCERNET", "https://soccernet.ng/feed"),
    ("COMPLETE SPORTS", "https://www.completesports.com/feed/"),
    ("VANGUARD SPORTS", "https://www.vanguardngr.com/category/sports/feed/"),
    ("PUNCH SPORTS", "https://rss.punchng.com/v1/category/sports"),
    ("DAILY TRUST SPORTS", "https://dailytrust.com/category/sports/feed/"),
    ("THE SOUTH AFRICAN", "https://www.thesouthafrican.com/sport/soccer/feed/"),
    ("THE CITIZEN SPORT", "https://www.citizen.co.za/sport/feed/"),
    ("IOL SPORT", "https://www.iol.co.za/sport/soccer/feed/"),
    ("SOWETAN LIVE", "https://www.sowetanlive.co.za/sport/soccer/feed/"),
    ("TIMES LIVE SPORT", "https://www.timeslive.co.za/sport/soccer/feed/"),
    ("DAILY MAVERICK SPORT", "https://www.dailymaverick.co.za/section/sport/feed/"),
    ("GHANA WEB SPORTS", "https://www.ghanaweb.com/GhanaHomePage/SportsArchive/rss.xml"),
    ("MODERN GHANA SPORTS", "https://www.modernghana.com/rss/sports"),
    ("STAD EL AHLY", "https://www.stadelahly.net/feed/"),
    ("FILGOAL", "https://www.filgoal.com/rss/news"),
    ("DZ FOOT", "https://www.dzfoot.com/feed"),
    ("AL AHRAM SPORTS", "https://english.ahram.org.eg/rss/Sports"),
    ("NILE POST SPORT", "https://nilepost.co.ug/category/sports/feed/"),
    ("NEW TIMES RWANDA", "https://www.newtimes.co.rw/rss/sport"),
    ("CAPITAL FM SPORTS", "https://www.capitalfm.co.ke/sports/soccer/feed/"),
    ("STANDARD KENYA SPORT", "https://www.standardmedia.co.ke/category/38/sports/feed/"),
    ("DAILYNATION SPORT", "https://nation.africa/kenya/sports/soccer/rss"),
    ("CITIZEN DIGITAL SPORT", "https://www.citizen.digital/sports/football/rss"),
    ("BOTSWANA DAILY NEWS", "http://www.dailynews.gov.bw/rss/sports/"),
    ("NAMIBIAN SPORT", "https://www.namibian.com.na/category/sport/feed/"),

    # --- ADDITIONAL GLOBAL & NICHE ---
    ("BEYOND THE PITCH", "https://beyondthepitch.net/feed/"),
    ("FOOTBALL INSIDER", "https://www.footballinsider247.com/feed/"),
    ("THE KOP TIMES", "https://thekoptimes.com/feed/"),
    ("LIVE 4 LIVERPOOL", "https://live4liverpool.com/feed/"),
    ("FRIENDS OF LIVERPOOL", "https://friendsofliverpool.com/feed/"),
    ("ARSENAL INSIDER", "https://www.arsenalinsider.com/feed/"),
    ("MANUTD NEWS", "https://www.manutdnews.com/feed/"),
    ("CHELSEA NEWS", "https://www.chelseanews.com/feed/"),
    ("CITY XTRA", "https://cityxtra.co.uk/feed/"),
    ("JUST FOOTBALL", "http://feeds.feedburner.com/Just-football"),
    ("THESE FOOTBALL TIMES", "https://thesefootballtimes.co/feed/"),
    ("AMERICAN SOCCER ANALYSIS", "https://www.americansocceranalysis.com/home?format=rss"),
    ("SBI SOCCER", "https://sbisoccer.com/feed"),
    ("TOP DRAWER SOCCER", "https://www.topdrawersoccer.com/feed/"),
    ("WORLD SOCCER MAGAZINE", "https://www.worldsoccer.com/feed"),
    ("FOOTBALL ECONOMY", "https://www.footballeconomy.com/feed"),
    ("SOCCER AMERICA", "https://www.socceramerica.com/rss/news/"),
    ("PRO SOCCER WIRE", "https://prosoccerwire.usatoday.com/feed/"),
    ("SOCCER REPETITION", "https://soccerrepetition.com/feed/"),
    ("THE AWAY END", "https://theawayend.co/feed/")
]

# ────────────────────────────────────────────────
# SESSION STATE
# ────────────────────────────────────────────────
if "source_limit" not in st.session_state:
    st.session_state.source_limit = 10

if "article_limit" not in st.session_state:
    st.session_state.article_limit = 5

# ────────────────────────────────────────────────
# IMAGE SYSTEM
# ────────────────────────────────────────────────
def fetch_article_image(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=6)
        soup = BeautifulSoup(r.text, "html.parser")
        img = soup.find("meta", property="og:image")
        if img and img.get("content"):
            return img["content"]
    except:
        pass
    return None

def fetch_image(title, url):
    img = fetch_article_image(url)
    if img:
        return img
    return "https://images.unsplash.com/photo-1508098682722-e99c43a406b2"

# ────────────────────────────────────────────────
# SCRAPER
# ────────────────────────────────────────────────
def scrape(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        soup = BeautifulSoup(r.text, "html.parser")
        return " ".join(p.get_text() for p in soup.find_all("p")[:25])
    except:
        return None

# ────────────────────────────────────────────────
# HASHTAGS
# ────────────────────────────────────────────────
def generate_tags(text):
    try:
        words = re.findall(r"\b[A-Za-z]{5,}\b", text.lower())
        stop = set(nltk.corpus.stopwords.words("english"))
        common = Counter([w for w in words if w not in stop]).most_common(5)
        return [f"#{w.capitalize()}" for w, _ in common]
    except:
        return ["#Football", "#Soccer"]

# ────────────────────────────────────────────────
# SUMMARY
# ────────────────────────────────────────────────
def summarize(text, title):
    try:
        sentences = text.split(". ")
        summary = ". ".join(sentences[:2]) + "."
    except:
        summary = "Summary unavailable."

    tags = generate_tags(text)

    return f"""🔥 {title}

📝 {summary}

{' '.join(tags)}"""

# ────────────────────────────────────────────────
# TIME PARSER
# ────────────────────────────────────────────────
def parse_time(entry):
    try:
        # Supports published_parsed or regular strings
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
    except:
        pass
    return None

# ────────────────────────────────────────────────
# FEED ENGINE
# ────────────────────────────────────────────────
@st.cache_data(ttl=300)
def get_feed(source_limit):
    items = []
    fallback = []
    seen_links = set()

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=3) # Increased to 3 hours for better coverage

    for name, url in ALL_SOURCES[:source_limit]:
        try:
            feed = feedparser.parse(url)
            for e in feed.entries:
                link = getattr(e, "link", None)
                title = getattr(e, "title", "").upper()

                if not link or link in seen_links:
                    continue

                pub_time = parse_time(e)

                article = {
                    "title": title,
                    "link": link,
                    "source": name,
                    "time": pub_time.strftime("%H:%M") if pub_time else "N/A"
                }

                # Primary filter (Fresh news)
                if pub_time and pub_time >= cutoff:
                    items.append(article)
                    seen_links.add(link)
                else:
                    # Fallback store (Older news)
                    fallback.append(article)
                    seen_links.add(link)

        except:
            continue

    # 🚨 NEVER EMPTY FIX: If fresh news is empty, return fallbacks
    if len(items) == 0:
        return fallback[:source_limit * 2]

    return items

# ────────────────────────────────────────────────
# UI
# ────────────────────────────────────────────────
st.title("⚡ NEO-SCOUT v17.5")
st.caption("ULTRA-SOURCE SOCCER NEWS • 100+ GLOBAL & AFRICAN CHANNELS")

# Load Feed
feed = get_feed(st.session_state.source_limit)

# SEARCH/FILTER
search = st.text_input("📡 FILTER GLOBAL INTEL...", "").upper()
if search:
    feed = [f for f in feed if search in f["title"]]

# Limit View
visible_feed = feed[:st.session_state.article_limit]

# DISPLAY CARDS
for entry in visible_feed:
    with st.container():
        st.markdown("---")
        col1, col2 = st.columns([1, 2])
        
        with col1:
            img = fetch_image(entry["title"], entry["link"])
            st.image(img, use_container_width=True)
            
        with col2:
            st.subheader(entry["title"])
            st.caption(f"📡 {entry['source']} • ⏰ {entry['time']} UTC")
            st.markdown(f"[Read full article]({entry['link']})")

            # Expandable Summary to keep UI clean
            with st.expander("📝 Generate Social Post"):
                if st.button("🚀 Analyze Content", key=f"btn_{hashlib.md5(entry['link'].encode()).hexdigest()}"):
                    with st.spinner("Synthesizing..."):
                        text = scrape(entry["link"])
                        if text:
                            post = summarize(text, entry["title"])
                            st.code(post)
                        else:
                            st.error("Could not scrape article content.")

# ────────────────────────────────────────────────
# LOAD MORE
# ────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
col_load, _ = st.columns([1, 5])

with col_load:
    if st.button("⬇️ Load More News"):
        st.session_state.article_limit += 5
        
        # If we run out of articles, increase the source pool
        if st.session_state.article_limit > len(feed):
            st.session_state.source_limit = min(st.session_state.source_limit + 10, len(ALL_SOURCES))
            # Clear cache to fetch from new sources
            st.cache_data.clear()
            
        st.rerun()

# Sidebar Stats
st.sidebar.markdown("### 📊 System Status")
st.sidebar.write(f"Sources Active: {st.session_state.source_limit}/{len(ALL_SOURCES)}")
st.sidebar.write(f"Articles Loaded: {len(feed)}")
if st.sidebar.button("♻️ Refresh System"):
    st.cache_data.clear()
    st.rerun()
