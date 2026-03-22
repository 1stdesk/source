import streamlit as st
import feedparser
import requests
from bs4 import BeautifulSoup
import random

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Global 100 Soccer Scout", page_icon="⚽", layout="wide")

# --- 2. THE CONTINENTAL 20x5 SOURCE POOL ---
SOURCES_BY_CONTINENT = {
    "Europe": [
        ("BBC Sport", "http://newsrss.bbc.co.uk/rss/sportonline_uk_edition/football/rss.xml"),
        ("Sky Sports", "https://www.skysports.com/rss/12040"),
        ("The Guardian", "https://www.theguardian.com/football/rss"),
        ("Marca (ES)", "https://e00-marca.uecdn.es/rss/en/index.xml"),
        ("AS English", "https://en.as.com/rss/en/football/index.xml"),
        ("Football Italia", "https://football-italia.net/feed/"),
        ("Kicker (DE)", "https://www.kicker.de/news.rss"),
        ("France24 Sport", "https://www.france24.com/en/sports/rss"),
        ("EuroSport", "https://www.eurosport.com/football/rss.xml"),
        ("Football365", "https://www.football365.com/feed"),
        ("CaughtOffside", "https://www.caughtoffside.com/feed/"),
        ("TEAMtalk", "https://www.teamtalk.com/feed"),
        ("FourFourTwo", "https://www.fourfourtwo.com/rss.xml"),
        ("Mirror Football", "https://www.mirror.co.uk/sport/football/rss.xml"),
        ("Daily Mail", "https://www.dailymail.co.uk/sport/football/index.rss"),
        ("Independent", "https://www.independent.co.uk/sport/football/rss"),
        ("Irish Times", "https://www.irishtimes.com/cmlink/news-soccer-1.1319114"),
        ("Barca Universal", "https://barcauniversal.com/feed/"),
        ("Sempre Milan", "https://sempremilan.com/feed"),
        ("Arseblog", "https://arseblog.news/feed/")
    ],
    "Africa": [
        ("Soccer Laduma", "https://www.snl24.com/soccerladuma/rss"),
        ("KickOff", "https://www.snl24.com/kickoff/rss"),
        ("Ghana Soccernet", "https://ghanasoccernet.com/feed"),
        ("Sowetan Live", "https://www.sowetanlive.co.za/sport/soccer/rss"),
        ("iDiski Times", "https://www.idiskitimes.co.za/feed/"),
        ("FarPost", "https://farpost.co.za/feed/"),
        ("Soccernet NG", "https://soccernet.ng/feed/"),
        ("Brila FM", "https://www.brila.net/feed/"),
        ("CAF Online", "https://www.cafonline.com/rss"),
        ("The South African", "https://www.thesouthafrican.com/sport/soccer/feed/"),
        ("KingFut (EG)", "https://www.kingfut.com/feed/"),
        ("Daily Post NG", "https://dailypost.ng/sport/football/feed/"),
        ("Vanguard News", "https://www.vanguardngr.com/category/sports/football/feed/"),
        ("Ahram Online", "https://english.ahram.org.eg/rss/Sports.aspx"),
        ("Premium Times", "https://www.premiumtimesng.com/category/sports/football/feed"),
        ("AllAfrica Soccer", "https://allafrica.com/tools/headlines/rss/soccer/main.xml"),
        ("Cameroon News", "https://www.cameroon-info.net/rss/sport.xml"),
        ("Sports Kenya", "https://www.sportsnews.co.ke/feed/"),
        ("Maroc Football", "https://www.marocfootball.info/feed/"),
        ("Soka25East", "https://soka25east.com/feed/")
    ],
    "North America": [
        ("MLS Soccer", "https://www.mlssoccer.com/rss/news.xml"),
        ("ESPN FC", "https://www.espn.com/espn/rss/soccer/news"),
        ("SBI Soccer", "https://sbisoccer.com/feed"),
        ("TopDrawerSoccer", "https://www.topdrawersoccer.com/feed/"),
        ("World Soccer Talk", "https://worldsoccertalk.com/feed/"),
        ("American Soccer Analysis", "https://www.americansocceranalysis.com/home?format=rss"),
        ("Stars and Stripes FC", "https://www.starsandstripesfc.com/rss/current.xml"),
        ("The Athletic US", "https://theathletic.com/rss"),
        ("Sporting News", "https://www.sportingnews.com/us/rss/soccer"),
        ("FOX Sports Soccer", "https://api.foxsports.com/v2/content/optimized-rss?partnerKey=MB0ByRLeIIWqg9u9z6UHehfE6Zbd0vbd&tag=soccer"),
        ("CBS Sports Soccer", "https://www.cbssports.com/rss/headlines/soccer/"),
        ("Dirty South Soccer", "https://www.dirtysouthsoccer.com/rss/current.xml"),
        ("Hudson River Blue", "https://www.hudsonriverblue.com/rss/current.xml"),
        ("Sounder At Heart", "https://www.sounderatheart.com/rss/current.xml"),
        ("Brotherly Game", "https://www.brotherlygame.com/rss/current.xml"),
        ("Waking The Red", "https://www.wakingthered.com/rss/current.xml"),
        ("US Soccer", "https://www.ussoccer.com/rss/news.xml"),
        ("Canada Soccer", "https://canadasoccer.com/feed/"),
        ("Mexican Futbol", "https://mexicanfut.com/feed/"),
        ("SBNation Soccer", "https://www.sbnation.com/soccer/rss/current.xml")
    ],
    "South America": [
        ("Globo Esporte (BR)", "https://ge.globo.com/rss/ge/futebol/"),
        ("CONMEBOL", "https://www.conmebol.com/en/feed/"),
        ("Buenos Aires Times", "https://www.batimes.com.ar/feed/section/sports"),
        ("Lance!", "https://www.lance.com.br/rss/futebol"),
        ("Meridiano (VE)", "https://meridiano.net/rss/futbol"),
        ("La Tercera (CL)", "https://www.latercera.com/arc/outboundfeeds/rss/category/el-deportivo/"),
        ("El Comercio (PE)", "https://elcomercio.pe/arc/outboundfeeds/rss/category/deporte-total/futbol-peruano/"),
        ("Ovación (UY)", "https://www.elpais.com.uy/rss/ovacion"),
        ("Cancha (MX/SA)", "https://www.cancha.com/rss/futbol.xml"),
        ("Mundo D (AR)", "https://www.lavoz.com.ar/rss/mundo-d/"),
        ("ZeroZero (PT/BR)", "https://www.zerozero.pt/rss/noticias.php"),
        ("Futbol Red (CO)", "https://www.futbolred.com/rss"),
        ("Gol Caracol", "https://noticias.caracoltv.com/rss/deportes"),
        ("El Universo (EC)", "https://www.eluniverso.com/arc/outboundfeeds/rss/category/deportes/"),
        ("Gazeta Esportiva", "https://www.gazetaesportiva.com/feed/"),
        ("Tyc Sports", "https://www.tycsports.com/rss/rss.xml"),
        ("UOL Esporte", "https://rss.uol.com.br/feed/esporte.xml"),
        ("Soccerway LatAm", "https://za.soccerway.com/rss/"),
        ("Bolavip", "https://bolavip.com/en/rss"),
        ("BeSoccer LatAm", "https://pt.besoccer.com/rss/noticias")
    ],
    "Asia & Oceania": [
        ("The Asian Game", "https://www.theasiangame.com/feed/"),
        ("Japan Times Soccer", "https://www.japantimes.co.jp/sports/soccer/feed/"),
        ("CNA Sport (Asia)", "https://www.channelnewsasia.com/rssfeeds/8395966"),
        ("The Roar (AU)", "https://www.theroar.com.au/football/feed/"),
        ("FTBL Australia", "https://www.ftbl.com.au/rss"),
        ("KeepUp (A-League)", "https://keepup.com.au/feed/"),
        ("Oceania Football", "https://www.oceaniafootball.com/feed/"),
        ("Vanuatu Daily Post", "https://www.dailypost.vu/search/?f=rss&t=article&l=10&c=sports/football"),
        ("Sina Sports (CN)", "http://sports.sina.com.cn/rss/soccer.xml"),
        ("Yonhap (KR)", "https://en.yna.co.kr/RSS/sport.xml"),
        ("Football Federation Australia", "https://www.footballaustralia.com.au/rss/news"),
        ("New Zealand Football", "https://www.nzfootball.co.nz/rss/news"),
        ("Al Jazeera Sport", "https://www.aljazeera.com/xml/rss/all.xml"),
        ("The Peninsula (QA)", "https://thepeninsulaqatar.com/rss/section/55"),
        ("Saudigazette", "https://saudigazette.com.sa/rss/Section/61"),
        ("Football Pakistan", "https://www.footballpakistan.com/feed/"),
        ("Goal Nepal", "https://www.goalnepal.com/rss/news"),
        ("VietNamNet Sport", "https://vietnamnet.vn/rss/the-thao.rss"),
        ("Thai PBS World", "https://www.thaipbsworld.com/category/sport/feed/"),
        ("World Football Index (Asia)", "https://worldfootballindex.com/category/asia/feed/")
    ]
}

# Flatten the list for the queue system while keeping continent labels
FLATTENED_SOURCES = []
for continent, list_of_sources in SOURCES_BY_CONTINENT.items():
    for name, url in list_of_sources:
        FLATTENED_SOURCES.append((name, url, continent))

# --- 3. QUEUE SYSTEM (ZERO-REPEAT) ---
if 'source_queue' not in st.session_state:
    all_s = FLATTENED_SOURCES.copy()
    random.shuffle(all_s)
    st.session_state.source_queue = all_s
    st.session_state.queue_index = 0

def fetch_next_20():
    if st.session_state.queue_index + 20 > len(st.session_state.source_queue):
        random.shuffle(st.session_state.source_queue)
        st.session_state.queue_index = 0
    selected = st.session_state.source_queue[st.session_state.queue_index : st.session_state.queue_index + 20]
    st.session_state.queue_index += 20
    
    data = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    for name, url, continent in selected:
        try:
            f = feedparser.parse(url)
            if f.entries:
                e = f.entries[0]
                r = requests.get(e.link, headers=headers, timeout=1.5)
                soup = BeautifulSoup(r.content, 'html.parser')
                img = soup.find("meta", property="og:image")
                img_url = img["content"] if img else "https://via.placeholder.com/400x225?text=Soccer+Scout"
                data.append({"s": name, "t": e.title, "l": e.link, "img": img_url, "c": continent})
        except: continue
    return data

def get_detailed_context(url):
    try:
        r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=3)
        soup = BeautifulSoup(r.content, 'html.parser')
        paras = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text()) > 90]
        return paras[0] if paras else "Full details are available at the official source."
    except: return "Details are currently being updated by the newsroom."

# --- 4. UI INTERFACE ---
st.title("⚽ GLOBAL SOCCER HUB: 100 SOURCE NETWORK")
st.caption(f"Spanning 5 Continents. Progress: {st.session_state.queue_index}/{len(FLATTENED_SOURCES)}")

if 'visual_feed' not in st.session_state:
    st.session_state.visual_feed = fetch_next_20()

m_col, s_col = st.columns([4, 1.2])

with m_col:
    grid = st.columns(4)
    for idx, item in enumerate(st.session_state.visual_feed):
        with grid[idx % 4]:
            st.markdown(f'''
                <div style="background:#111; border-radius:12px; border:1px solid #333; margin-bottom:12px; height:400px; overflow:hidden;">
                    <img src="{item['img']}" style="width:100%; height:160px; object-fit:cover;">
                    <div style="padding:10px;">
                        <p style="color:#00ff41; font-size:10px; font-weight:bold; margin:0;">{item['c'].upper()} | {item['s'].upper()}</p>
                        <p style="font-size:12px; font-weight:bold; color:white; margin-top:5px; height:60px; overflow:hidden;">{item['t']}</p>
                        <a href="{item['l']}" target="_blank" style="color:#888; font-size:10px; text-decoration:none;">🔗 Official Article</a>
                    </div>
                </div>
            ''', unsafe_allow_html=True)
            if st.button("🎤 DEEP SCOOP", key=f"btn_{idx}", use_container_width=True):
                st.session_state.active = item

with s_col:
    st.markdown("### 🔥 Trending #Tags")
    for t in ["#WorldCup2026", "#RespectTheWork", "#ContinentalClash", "#HereWeGo"]:
        st.markdown(f'<div style="background:#111; padding:10px; border-radius:8px; margin-bottom:8px; border-left:3px solid #00ff41; color:white; font-size:13px;">{t}</div>', unsafe_allow_html=True)
    if st.button("🔄 REFRESH: SHOW NEW", use_container_width=True):
        st.session_state.visual_feed = fetch_next_20()
        st.rerun()

# --- 5. THE "RESPECT THE WORK" GENERATOR ---
if 'active' in st.session_state:
    it = st.session_state.active
    st.divider()
    with st.spinner(f"Analyzing {it['c']} tactical radiography..."):
        full_context = get_detailed_context(it['l'])
        
        scoop_response = (
            f"Broadcasting from the **{it['c']}** desk... We always find something to say about **{it['s']}**... but let’s be honest 🗣️\n\n"
            f"Every time they hit the headlines with news like **\"{it['t']}\"**, the quality and consistency keep coming! 📈\n\n"
            f"Maybe it’s time we give credit where it’s due. **The context:** {full_context[:300]}...\n\n"
            f"Solid, reliable, and always stepping up when it matters! Respect the silent work! 🛡️💎\n\n"
            f"👇 **FULL BREAKDOWN HERE:**\n"
            f"{it['l']}\n\n"
            f"#{it['s'].replace(' ', '')} #Soccer_{it['c']} #RespectTheWork #FootballUpdate #GameChanger"
        )
        
        st.subheader(f"Insider Deep Scoop: {it['s']} ({it['c']})")
        st.code(scoop_response, language="markdown")
