"""
Lists every channel currently inside the Telegram folder, one per line as
"<id>\t<title>\t<username or ->". Read-only, doesn't touch state.json.

Used to detect newly added channels: compare this output's IDs against
the IDs already tracked in state.json. Any ID not in state.json is new.
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

    with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
        entities = get_folder_entities(client, folder_name)
        print(f"CHANNEL_COUNT={len(entities)}")
        for entity in entities:
            label = getattr(entity, "title", None) or getattr(entity, "username", None) or str(entity.id)
            username = getattr(entity, "username", None) or "-"
            print(f"{entity.id}\t{label}\t{username}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
