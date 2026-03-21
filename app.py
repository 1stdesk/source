import tkinter as tk
from tkinter import ttk
import feedparser, webbrowser, threading, requests, random, queue

# --- MASTER POOL (Add as many as you want here) ---
# The script will pick a random selection from this list every time.
MASTER_SOURCES = [
    # SOUTH AFRICA
    ("Soccer Laduma", "https://www.snl24.com/soccerladuma/rss"),
    ("KickOff", "https://www.snl24.com/kickoff/rss"),
    ("Daily Sun Sport", "https://www.snl24.com/dailysun/sport/rss"),
    ("SuperSport", "https://supersport.com/rss/football"),
    ("Sowetan Live", "https://www.sowetanlive.co.za/sport/soccer/rss"),
    # EUROPE / UK
    ("BBC Football", "https://push.api.bbci.co.uk/morph/items?page=1&limit=10&feed=football"),
    ("Sky Sports", "https://www.skysports.com/rss/12040"),
    ("The Guardian", "https://www.theguardian.com/football/rss"),
    ("Independent", "https://www.independent.co.uk/sport/football/rss"),
    ("Daily Mail", "https://www.dailymail.co.uk/sport/football/index.rss"),
    ("Evening Standard", "https://www.standard.co.uk/sport/football/rss"),
    # EUROPE / GLOBAL
    ("Goal.com", "https://www.goal.com/en/feeds/news"),
    ("Transfermarkt", "https://www.transfermarkt.com/rss/news"),
    ("Marca (Spain)", "https://e00-marca.uecdn.es/rss/en/index.xml"),
    ("AS (Spain)", "https://en.as.com/rss/en/football/index.xml"),
    ("Football Italia", "https://football-italia.net/feed/"),
    ("90min", "https://www.90min.com/posts.rss"),
    ("CaughtOffside", "https://www.caughtoffside.com/feed/"),
    ("OneFootball", "https://onefootball.com/en/rss"),
    ("World Soccer Talk", "https://worldsoccertalk.com/feed/"),
    # GOOGLE NEWS SEARCHES (Strictly Football)
    ("Google News: PSL", "https://news.google.com/rss/search?q=PSL+football+when:1h&hl=en-ZA&gl=ZA"),
    ("Google News: Transfers", "https://news.google.com/rss/search?q=football+transfers+when:1h&hl=en-ZA&gl=ZA"),
    ("Google News: Champions League", "https://news.google.com/rss/search?q=UEFA+Champions+League+when:1h&hl=en-ZA&gl=ZA")
]

class DynamicFootballHub:
    def __init__(self, root):
        self.root = root
        self.root.title("Dynamic Football Monitor 2026")
        self.root.geometry("850x850")
        self.root.configure(bg="#050505")
        self.q = queue.Queue()

        # Header
        self.nav = tk.Frame(root, bg="#111", pady=15)
        self.nav.pack(fill="x")
        tk.Label(self.nav, text="⚽ DYNAMIC 20 FEED", font=("Impact", 24), bg="#111", fg="#00ff41").pack(side="left", padx=20)
        
        self.btn = tk.Button(self.nav, text="🔄 GRAB NEW SOURCES", bg="#00ff41", fg="black", 
                            font=("Arial", 10, "bold"), command=self.refresh)
        self.btn.pack(side="right", padx=20)

        # Scrollable UI
        self.canvas = tk.Canvas(root, bg="#050505", highlightthickness=0)
        self.frame = tk.Frame(self.canvas, bg="#050505")
        self.sb = ttk.Scrollbar(root, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.sb.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.sb.pack(side="right", fill="y")
        self.canvas.create_window((0,0), window=self.frame, anchor="nw", width=830)
        self.frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.root.after(100, self.update_check)
        self.refresh()

    def refresh(self):
        self.btn.config(text="🔀 SHUFFLING...", state="disabled")
        for w in self.frame.winfo_children(): w.destroy()
        threading.Thread(target=self.fetch_worker, daemon=True).start()

    def fetch_worker(self):
        # 1. Randomize the master pool
        shuffled_pool = list(MASTER_SOURCES)
        random.shuffle(shuffled_pool)
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        news_to_show = []
        
        # 2. Loop through the randomized sources until we have 20 headlines
        for name, url in shuffled_pool:
            if len(news_to_show) >= 20: break
            try:
                # Add cache buster to URL
                cb_url = f"{url}&cb={random.random()}" if "?" in url else f"{url}?cb={random.random()}"
                r = requests.get(cb_url, headers=headers, timeout=5)
                f = feedparser.parse(r.content)
                
                # Take only the newest 1-2 stories from this source to ensure variety
                for e in f.entries[:2]:
                    if len(news_to_show) >= 20: break
                    news_to_show.append({'s': name, 't': e.title.rsplit(' - ', 1)[0], 'l': e.link})
            except: continue
            
        self.q.put(news_to_show)

    def update_check(self):
        try:
            while not self.q.empty():
                items = self.q.get_nowait()
                for idx, i in enumerate(items, 1):
                    card = tk.Frame(self.frame, bg="#121212", pady=10, padx=15, highlightbackground="#333", highlightthickness=1)
                    card.pack(fill="x", pady=3, padx=10)
                    tk.Label(card, text=f"{idx}. {i['s'].upper()}", fg="#00ff41", bg="#121212", font=("Arial", 7, "bold")).pack(anchor="w")
                    t = tk.Label(card, text=i['t'], fg="white", bg="#121212", font=("Arial", 11, "bold"), wraplength=780, justify="left", cursor="hand2")
                    t.pack(anchor="w", pady=5)
                    t.bind("<Button-1>", lambda e, l=i['l']: webbrowser.open(l))
                self.btn.config(text="🔄 GRAB NEW SOURCES", state="normal")
        except: pass
        self.root.after(500, self.update_check)

if __name__ == "__main__":
    root = tk.Tk()
    app = DynamicFootballHub(root)
    root.mainloop()