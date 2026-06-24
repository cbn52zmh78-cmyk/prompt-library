import os
import sys
from pathlib import Path

sys.path.insert(0, r"C:\Users\NCG\Videos\Grok Projects\tools")
env = Path(r"C:\Users\NCG\Videos\Grok Projects\.env")
if env.exists():
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

import tweepy

client = tweepy.Client(
    consumer_key=os.environ.get("X_API_KEY", ""),
    consumer_secret=os.environ.get("X_API_SECRET", ""),
    access_token=os.environ.get("X_ACCESS_TOKEN", ""),
    access_token_secret=os.environ.get("X_ACCESS_TOKEN_SECRET", ""),
    bearer_token=os.environ.get("X_BEARER_TOKEN", ""),
)

queries = [
    "n8n hiring contractor",
    "claude api freelance",
    "langchain contractor",
    "crewai hiring",
    "ai agent contractor",
]
for q in queries:
    print("===", q, "===")
    try:
        resp = client.search_recent_tweets(
            query=f"{q} -is:retweet lang:en",
            max_results=10,
            tweet_fields=["created_at", "author_id"],
        )
        if resp.data:
            for t in resp.data:
                print(t.created_at, "|", t.text[:220].replace("\n", " "))
        else:
            print("No results")
    except Exception as e:
        print("ERR:", e)
    print()