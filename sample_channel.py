"""
Prints the last N raw posts (unfiltered - no keyword matching) from one or
more specific channels, for format analysis when a channel is newly added
to the folder. Read-only, doesn't touch state.json.

  SAMPLE_CHANNEL_IDS  - comma-separated Telegram channel/chat IDs to
                        sample (as reported by list_channels.py)
  SAMPLE_COUNT        - optional, defaults to 5

Entities are resolved via the folder's dialog filter (same as
list_channels.py / watch.py), not by a bare numeric ID lookup - a fresh
session has no cached entities, and Telethon can't resolve a PeerUser
(a bot or regular user account, as opposed to a broadcast channel) from
just its ID without that cache.
"""
import os
import sys

from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import GetDialogFiltersRequest


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
            print(f"Could not resolve a peer in folder '{folder_name}': {e}", file=sys.stderr)
    return entities


def main() -> int:
    api_id = int(os.environ["TG_API_ID"])
    api_hash = os.environ["TG_API_HASH"]
    session_string = os.environ["TG_SESSION"]
    folder_name = os.environ.get("FOLDER_NAME", "Vacancies")
    wanted_ids = {c.strip() for c in os.environ["SAMPLE_CHANNEL_IDS"].split(",") if c.strip()}
    count = int(os.environ.get("SAMPLE_COUNT", "5"))

    with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
        entities = get_folder_entities(client, folder_name)
        by_id = {str(e.id): e for e in entities}

        for channel_id in wanted_ids:
            entity = by_id.get(channel_id)
            if entity is None:
                print(f"\n===== id={channel_id}: not found in folder '{folder_name}' =====")
                continue

            label = getattr(entity, "title", None) or getattr(entity, "username", None) or channel_id
            username = getattr(entity, "username", None)
            entity_type = type(entity).__name__

            print(f"\n===== {label} (id={channel_id}, type={entity_type}) =====")
            try:
                messages = list(client.iter_messages(entity, limit=count))
            except Exception as e:
                print(f"Could not fetch messages: {e}")
                continue

            if not messages:
                print("(no messages found)")
                continue

            for m in messages:
                text = (m.message or "").strip()
                link = f"https://t.me/{username}/{m.id}" if username else "(private/no public link)"
                print(f"--- {m.date.isoformat()} {link} ---")
                print(text if text else "(no text / media-only post)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
