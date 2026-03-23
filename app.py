def get_feed(limit):
    items = []
    fallback_items = []
    seen_links = set()

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=2)

    for name, url in ALL_SOURCES[:limit]:
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

                # ✅ PRIMARY (last 2 hours)
                if pub_time and pub_time >= cutoff:
                    items.append(article)
                    seen_links.add(link)
                    break

                # ✅ FALLBACK (store anyway)
                fallback_items.append(article)

        except:
            continue

    # 🚨 KEY FIX
    if len(items) == 0:
        return fallback_items[:limit]

    return items
