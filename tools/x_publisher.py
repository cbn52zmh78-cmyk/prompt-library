#!/usr/bin/env python3
"""
X Publisher — post tweets and send DMs via official API (OAuth 1.0a user context).

Requires app permissions: Read and write and Direct message.
Credentials: ~/Videos/Grok Projects/.env (four OAuth 1.0a tokens).
"""

from __future__ import annotations

import _bootstrap  # noqa: F401

import json
import os
import sys
from datetime import datetime
from workspace_paths import (
    ENV_EXAMPLE_FILE,
    ENV_FILE,
    X_DM_QUEUE_FILE,
    X_QUEUE_FILE,
)

QUEUE_FILE = X_QUEUE_FILE
DM_QUEUE_FILE = X_DM_QUEUE_FILE

REQUIRED_KEYS = (
    "X_API_KEY",
    "X_API_SECRET",
    "X_ACCESS_TOKEN",
    "X_ACCESS_TOKEN_SECRET",
)

DM_MAX_CHARS = 10000
TWEET_MAX_CHARS = 280


def load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def missing_keys() -> list[str]:
    return [k for k in REQUIRED_KEYS if not os.environ.get(k)]


def get_client():
    missing = missing_keys()
    if missing:
        raise RuntimeError(
            "Missing API credentials: "
            + ", ".join(missing)
            + f"\nCopy {ENV_EXAMPLE_FILE} to {ENV_FILE} and fill in values."
        )

    import tweepy

    return tweepy.Client(
        consumer_key=os.environ["X_API_KEY"],
        consumer_secret=os.environ["X_API_SECRET"],
        access_token=os.environ["X_ACCESS_TOKEN"],
        access_token_secret=os.environ["X_ACCESS_TOKEN_SECRET"],
    )


def resolve_participant_id(client, recipient: str) -> str:
    recipient = recipient.strip().lstrip("@")
    if recipient.isdigit():
        return recipient
    response = client.get_user(username=recipient)
    if not response.data:
        raise RuntimeError(f"User @{recipient} not found.")
    return str(response.data.id)


def cmd_verify() -> int:
    load_env_file(ENV_FILE)
    try:
        client = get_client()
        me = client.get_me(user_fields=["username", "name", "verified"])
        user = me.data
        print(f"✅ Connected as @{user.username} ({user.name})")
        if getattr(user, "verified", None):
            print("   Verified account")
        print("   Permissions needed: Read and write and Direct message")
        print("   Capabilities: post tweets, send DMs (on your command)")
        return 0
    except Exception as exc:
        print(f"❌ Connection failed: {exc}")
        print("\nEnsure OAuth 1.0a tokens were regenerated after enabling DM permissions.")
        print(f"Credentials file: {ENV_FILE}")
        return 1


def load_queue(path: Path) -> list[dict]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []


def save_queue(path: Path, items: list[dict]) -> None:
    path.write_text(json.dumps(items, indent=2), encoding="utf-8")


def cmd_queue_add(text: str) -> int:
    items = load_queue(QUEUE_FILE)
    item = {
        "id": len(items) + 1,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "text": text,
        "status": "pending",
    }
    items.append(item)
    save_queue(QUEUE_FILE, items)
    print(f"Queued post #{item['id']} ({len(text)} chars)")
    return 0


def cmd_queue_list() -> int:
    items = load_queue(QUEUE_FILE)
    if not items:
        print("Post queue empty.")
        return 0
    for item in items:
        icon = "✅" if item.get("status") == "posted" else "⏳"
        preview = item["text"][:80].replace("\n", " ")
        if len(item["text"]) > 80:
            preview += "..."
        print(f"{icon} #{item['id']} [{item.get('status', 'pending')}] {preview}")
    return 0


def cmd_publish(post_id: int | None = None, dry_run: bool = False) -> int:
    load_env_file(ENV_FILE)
    items = load_queue(QUEUE_FILE)
    pending = [i for i in items if i.get("status") == "pending"]
    if not pending:
        print("No pending posts in queue.")
        return 1

    target = pending[0] if post_id is None else next(
        (i for i in pending if i["id"] == post_id), None
    )
    if not target:
        print(f"Pending post #{post_id} not found.")
        return 1

    text = target["text"]
    if len(text) > TWEET_MAX_CHARS:
        print(f"❌ Post is {len(text)} chars (max {TWEET_MAX_CHARS}).")
        return 1

    if dry_run:
        print(f"[dry-run] Would post #{target['id']}:\n{text}")
        return 0

    try:
        client = get_client()
        response = client.create_tweet(text=text)
        tweet_id = response.data["id"]
        target["status"] = "posted"
        target["tweet_id"] = str(tweet_id)
        target["posted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        save_queue(QUEUE_FILE, items)
        print(f"✅ Posted #{target['id']} → https://x.com/i/web/status/{tweet_id}")
        return 0
    except Exception as exc:
        print(f"❌ Publish failed: {exc}")
        return 1


def cmd_post_now(text: str, dry_run: bool = False) -> int:
    load_env_file(ENV_FILE)
    if len(text) > TWEET_MAX_CHARS:
        print(f"❌ Post is {len(text)} chars (max {TWEET_MAX_CHARS}).")
        return 1
    if dry_run:
        print(f"[dry-run] Would post:\n{text}")
        return 0
    try:
        client = get_client()
        response = client.create_tweet(text=text)
        tweet_id = response.data["id"]
        print(f"✅ Posted → https://x.com/i/web/status/{tweet_id}")
        return 0
    except Exception as exc:
        print(f"❌ Publish failed: {exc}")
        return 1


def cmd_dm_send(recipient: str, text: str, dry_run: bool = False) -> int:
    load_env_file(ENV_FILE)
    if len(text) > DM_MAX_CHARS:
        print(f"❌ DM is {len(text)} chars (max {DM_MAX_CHARS}).")
        return 1
    if dry_run:
        print(f"[dry-run] Would DM @{recipient.lstrip('@')}:\n{text}")
        return 0
    try:
        client = get_client()
        participant_id = resolve_participant_id(client, recipient)
        response = client.create_dm(participant_id=participant_id, text=text)
        data = response.data or {}
        conv_id = data.get("dm_conversation_id", data.get("dm_event_id", "ok"))
        print(f"✅ DM sent to @{recipient.lstrip('@')} (ref {conv_id})")
        return 0
    except Exception as exc:
        print(f"❌ DM failed: {exc}")
        return 1


def cmd_dm_queue_add(recipient: str, text: str) -> int:
    items = load_queue(DM_QUEUE_FILE)
    item = {
        "id": len(items) + 1,
        "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "recipient": recipient.lstrip("@"),
        "text": text,
        "status": "pending",
    }
    items.append(item)
    save_queue(DM_QUEUE_FILE, items)
    print(f"Queued DM #{item['id']} → @{item['recipient']} ({len(text)} chars)")
    return 0


def cmd_dm_queue_list() -> int:
    items = load_queue(DM_QUEUE_FILE)
    if not items:
        print("DM queue empty.")
        return 0
    for item in items:
        icon = "✅" if item.get("status") == "sent" else "⏳"
        preview = item["text"][:60].replace("\n", " ")
        if len(item["text"]) > 60:
            preview += "..."
        print(
            f"{icon} #{item['id']} → @{item['recipient']} "
            f"[{item.get('status', 'pending')}] {preview}"
        )
    return 0


def cmd_dm_publish(dm_id: int | None = None, dry_run: bool = False) -> int:
    load_env_file(ENV_FILE)
    items = load_queue(DM_QUEUE_FILE)
    pending = [i for i in items if i.get("status") == "pending"]
    if not pending:
        print("No pending DMs in queue.")
        return 1

    target = pending[0] if dm_id is None else next(
        (i for i in pending if i["id"] == dm_id), None
    )
    if not target:
        print(f"Pending DM #{dm_id} not found.")
        return 1

    recipient = target["recipient"]
    text = target["text"]
    if dry_run:
        print(f"[dry-run] Would DM @{recipient}:\n{text}")
        return 0

    try:
        client = get_client()
        participant_id = resolve_participant_id(client, recipient)
        response = client.create_dm(participant_id=participant_id, text=text)
        target["status"] = "sent"
        data = response.data or {}
        target["conversation_id"] = data.get(
            "dm_conversation_id", data.get("dm_event_id")
        )
        target["sent_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        save_queue(DM_QUEUE_FILE, items)
        print(f"✅ DM #{target['id']} sent to @{recipient}")
        return 0
    except Exception as exc:
        print(f"❌ DM failed: {exc}")
        return 1


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print(
            "Usage:\n"
            "  x_publisher.py verify\n"
            '  x_publisher.py post "Tweet text" [--dry-run]\n'
            '  x_publisher.py queue add "Tweet text"\n'
            "  x_publisher.py queue list\n"
            "  x_publisher.py publish [--id N] [--dry-run]\n"
            '  x_publisher.py dm @username "Message text" [--dry-run]\n'
            '  x_publisher.py dm queue add @username "Message text"\n'
            "  x_publisher.py dm queue list\n"
            "  x_publisher.py dm publish [--id N] [--dry-run]"
        )
        return 1

    cmd = argv[0]
    dry_run = "--dry-run" in argv

    if cmd == "verify":
        return cmd_verify()

    if cmd == "queue" and len(argv) >= 2:
        sub = argv[1]
        if sub == "add" and len(argv) >= 3:
            return cmd_queue_add(argv[2])
        if sub == "list":
            return cmd_queue_list()

    if cmd == "publish":
        post_id = None
        if "--id" in argv:
            idx = argv.index("--id")
            if idx + 1 < len(argv):
                post_id = int(argv[idx + 1])
        return cmd_publish(post_id=post_id, dry_run=dry_run)

    if cmd == "post" and len(argv) >= 2:
        return cmd_post_now(argv[2], dry_run=dry_run)

    if cmd == "dm":
        args = [a for a in argv[1:] if a != "--dry-run"]
        if not args:
            print("DM commands: @user message | queue add | queue list | publish")
            return 1

        if args[0] == "queue" and len(args) >= 2:
            sub = args[1]
            if sub == "add" and len(args) >= 4:
                return cmd_dm_queue_add(args[2], args[3])
            if sub == "list":
                return cmd_dm_queue_list()
            if sub == "publish":
                dm_id = None
                if "--id" in argv:
                    idx = argv.index("--id")
                    if idx + 1 < len(argv):
                        dm_id = int(argv[idx + 1])
                return cmd_dm_publish(dm_id=dm_id, dry_run=dry_run)

        if args[0] == "publish":
            dm_id = None
            if "--id" in argv:
                idx = argv.index("--id")
                if idx + 1 < len(argv):
                    dm_id = int(argv[idx + 1])
            return cmd_dm_publish(dm_id=dm_id, dry_run=dry_run)

        if len(args) >= 2 and args[0].startswith("@"):
            return cmd_dm_send(args[0], args[1], dry_run=dry_run)

    print("Unknown command or wrong arguments.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())