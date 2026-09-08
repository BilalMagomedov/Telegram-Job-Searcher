"""
Prints the last N raw posts (unfiltered - no keyword matching) from one or
more specific channels, for format analysis when a channel is newly added
to the folder. Read-only, doesn't touch state.json.

  SAMPLE_CHANNEL_IDS  - comma-separated Telegram channel/chat IDs to
                        sample (as reported by list_channels.py)
  SAMPLE_COUNT        - optional, defaults to 5
"""
import os
import sys

from telethon.sync import TelegramClient
from telethon.sessions import StringSession


def main() -> int:
    api_id = int(os.environ["TG_API_ID"])
    api_hash = os.environ["TG_API_HASH"]
    session_string = os.environ["TG_SESSION"]
    channel_ids = [c.strip() for c in os.environ["SAMPLE_CHANNEL_IDS"].split(",") if c.strip()]
    count = int(os.environ.get("SAMPLE_COUNT", "5"))

    with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
        for channel_id in channel_ids:
            entity = client.get_entity(int(channel_id))
            label = getattr(entity, "title", None) or getattr(entity, "username", None) or channel_id
            username = getattr(entity, "username", None)

            print(f"\n===== {label} (id={channel_id}) =====")
            for m in client.iter_messages(entity, limit=count):
                text = (m.message or "").strip()
                link = f"https://t.me/{username}/{m.id}" if username else "(private channel, no link)"
                print(f"--- {m.date.isoformat()} {link} ---")
                print(text if text else "(no text / media-only post)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
