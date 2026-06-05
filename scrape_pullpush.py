"""No-auth historical Reddit scraper via PullPush (api.pullpush.io).

PullPush is a community archive of Reddit comments & posts with full-text
search and NO authentication. Ideal for backfilling past patient trial
experiences. For ongoing NEW posts, use the live Reddit API (scrape_reddit.py)
once API access is granted.

Usage:
    python scrape_pullpush.py                  # all search terms, comments+posts
    python scrape_pullpush.py "phase 1 trial"  # one ad-hoc query
"""
import sys
import time

import requests

import config
import db

BASE = "https://api.pullpush.io/reddit/search"
HEADERS = {"User-Agent": "trial-voices/0.1"}
PAGE = 100  # max per request


def relevant(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in config.RELEVANCE_KEYWORDS)


def fetch(kind, query, before=None):
    """kind: 'comment' or 'submission'. Returns list of raw dicts."""
    params = {"q": query, "size": PAGE, "sort": "desc", "sort_type": "created_utc"}
    if before:
        params["before"] = before
    r = requests.get(f"{BASE}/{kind}/", params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json().get("data", [])


def harvest(conn, kind, query, max_pages=10):
    """Page backwards through time for one query+kind."""
    before = None
    added = 0
    for _ in range(max_pages):
        try:
            rows = fetch(kind, query, before)
        except Exception as e:
            print(f"    !! {kind} '{query}' page failed: {e}")
            break
        if not rows:
            break
        for x in rows:
            body = x.get("body") or x.get("selftext") or ""
            title = x.get("title")
            blob = f"{title or ''}\n{body}"
            if not relevant(blob):
                continue
            is_post = kind == "submission"
            rid = x.get("name") or (("t3_" if is_post else "t1_") + x.get("id", ""))
            db.upsert_document(conn, {
                "id": rid,
                "kind": "post" if is_post else "comment",
                "subreddit": x.get("subreddit", ""),
                "permalink": "https://reddit.com" + (x.get("permalink", "") or ""),
                "author": x.get("author", ""),
                "created_utc": x.get("created_utc", 0),
                "title": title,
                "body": body,
                "score": x.get("score", 0),
                "fetched_at": time.time(),
            })
            added += 1
        before = rows[-1].get("created_utc")  # paginate older
        conn.commit()
        time.sleep(1)  # be polite to the free archive
    return added


def main():
    db.init()
    conn = db.connect()
    queries = sys.argv[1:] or config.SEARCH_TERMS
    total = 0
    for q in queries:
        print(f"Query: '{q}'")
        for kind in ("comment", "submission"):
            n = harvest(conn, kind, q)
            print(f"  {kind}: +{n}")
            total += n
    conn.close()
    print(f"Done. {total} relevant docs upserted. Now: python extract.py submit")


if __name__ == "__main__":
    main()
