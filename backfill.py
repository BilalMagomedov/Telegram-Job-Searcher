"""
One-off historical scan: checks every channel inside the Telegram folder for
messages posted on a specific UTC calendar day, applying the same
KEYWORDS / EXCLUDE_KEYWORDS filters as watch.py, and prints matches.

This does NOT touch state.json and does NOT affect the regular incremental
watch.py schedule - it's a separate, read-only lookup for a given day.

Needs the same environment variables as watch.py, plus:

  BACKFILL_DATE  - the UTC calendar day to scan, format YYYY-MM-DD,
                   e.g. "2026-09-07"
"""
import os
import sys
from datetime import datetime, timedelta, timezone

from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import GetDialogFiltersRequest

SNIPPET_LEN = 300


def _title_text(title) -> str:
    if title is None:
        return ""
    if isinstance(title, str):
        return title
    return getattr(title, "text", "") or ""


def get_folder_entities(client: TelegramClient, folder_name: str) -> list:
    result = client(GetDialogFiltersRequest())
    filters = getattr(result, "filters", result)

    target = None
    for f in filters:
        if _title_text(getattr(f, "title", None)).strip().lower() == folder_name.strip().lower():
            target = f
            break

    if target is None or not hasattr(target, "include_peers"):
        return []

    entities = []
    for peer in target.include_peers:
        try:
            entities.append(client.get_entity(peer))
        except Exception as e:
            print(f"Could not resolve a peer in folder '{folder_name}': {e}")
    return entities


def main() -> int:
    api_id = int(os.environ["TG_API_ID"])
    api_hash = os.environ["TG_API_HASH"]
    session_string = os.environ["TG_SESSION"]
    folder_name = os.environ.get("FOLDER_NAME", "Vacancies")
    keywords = [k.strip().lower() for k in os.environ["KEYWORDS"].split(",") if k.strip()]
    exclude_keywords = [k.strip().lower() for k in os.environ.get("EXCLUDE_KEYWORDS", "").split(",") if k.strip()]

    day_start = datetime.strptime(os.environ["BACKFILL_DATE"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
    day_end = day_start + timedelta(days=1)

    matches = []

    with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
        entities = get_folder_entities(client, folder_name)
        if not entities:
            print(f"Folder '{folder_name}' not found or empty.")
            return 0

        print(f"Scanning {len(entities)} chat(s) in folder '{folder_name}' for {day_start.date()} (UTC).")

        for entity in entities:
            channel_label = getattr(entity, "title", None) or getattr(entity, "username", None) or str(entity.id)

            for m in client.iter_messages(entity, offset_date=day_end):
                if m.date < day_start:
                    break  # walked past the start of the target day, done with this channel
                if m.date >= day_end:
                    continue

                text = (m.message or "").strip()
                if not text:
                    continue
                lower = text.lower()
                if any(kw in lower for kw in keywords) and not any(kw in lower for kw in exclude_keywords):
                    username = getattr(entity, "username", None)
                    link = f"https://t.me/{username}/{m.id}" if username else "(private channel, no link)"
                    snippet = text[:SNIPPET_LEN] + ("..." if len(text) > SNIPPET_LEN else "")
                    matches.append((channel_label, m.date.isoformat(), link, snippet))

    print(f"\nFound {len(matches)} match(es) on {day_start.date()}:\n")
    for channel_label, date_iso, link, snippet in matches:
        print(f"[{channel_label}] {date_iso} {link}\n{snippet}\n---")

    return 0


if __name__ == "__main__":
    sys.exit(main())
