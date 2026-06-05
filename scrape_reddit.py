"""Resume-safe Reddit scraper. Idempotent: re-running only adds new docs.

Usage:
    python scrape_reddit.py            # all subreddits, all search terms
    python scrape_reddit.py cancer     # single subreddit
"""
import sys
import time

import praw

import config
import db


def relevant(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in config.RELEVANCE_KEYWORDS)


def make_reddit():
    if not config.REDDIT_CLIENT_ID:
        sys.exit("Set REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET env vars first.")
    return praw.Reddit(
        client_id=config.REDDIT_CLIENT_ID,
        client_secret=config.REDDIT_CLIENT_SECRET,
        user_agent=config.REDDIT_USER_AGENT,
    )


def scrape_subreddit(reddit, conn, sub_name, limit=200):
    sub = reddit.subreddit(sub_name)
    added = 0
    for term in config.SEARCH_TERMS:
        for post in sub.search(term, sort="relevance", time_filter="all", limit=limit):
            blob = f"{post.title}\n{post.selftext}"
            if relevant(blob):
                db.upsert_document(conn, {
                    "id": post.fullname, "kind": "post", "subreddit": sub_name,
                    "permalink": f"https://reddit.com{post.permalink}",
                    "author": str(post.author), "created_utc": post.created_utc,
                    "title": post.title, "body": post.selftext, "score": post.score,
                    "fetched_at": time.time(),
                })
                added += 1
            # Pull comments too — patient detail often lives there.
            post.comments.replace_more(limit=0)
            for c in post.comments.list():
                if relevant(c.body):
                    db.upsert_document(conn, {
                        "id": c.fullname, "kind": "comment", "subreddit": sub_name,
                        "permalink": f"https://reddit.com{c.permalink}",
                        "author": str(c.author), "created_utc": c.created_utc,
                        "title": None, "body": c.body, "score": c.score,
                        "fetched_at": time.time(),
                    })
                    added += 1
        conn.commit()
        print(f"  [{sub_name}] '{term}' -> {added} docs so far")
    return added


def main():
    db.init()
    conn = db.connect()
    reddit = make_reddit()
    subs = sys.argv[1:] or config.SUBREDDITS
    total = 0
    for s in subs:
        print(f"Scraping r/{s} ...")
        try:
            total += scrape_subreddit(reddit, conn, s)
        except Exception as e:  # keep going on per-sub failures
            print(f"  !! r/{s} failed: {e}")
    conn.close()
    print(f"Done. {total} relevant docs upserted.")


if __name__ == "__main__":
    main()
