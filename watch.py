"""
Scheduled watcher: checks every channel inside a specific Telegram folder
(default folder name: "Vacancies") for new messages containing any of your
keywords, and emails you a digest of matches.

The channel list is NOT hardcoded anywhere. It's read fresh from your
Telegram folder on every run - so adding a new channel to that folder from
your phone is the entire "setup" for a new source, no code or secrets to
touch.

Runs unattended (e.g. via GitHub Actions on a cron schedule). Needs these
environment variables (set as GitHub Actions secrets, see README.md):

  TG_API_ID           - from my.telegram.org
  TG_API_HASH         - from my.telegram.org
  TG_SESSION          - the string printed by login_once.py
  FOLDER_NAME         - optional, defaults to "Vacancies". The name of the
                        Telegram folder whose channels should be watched.
  GMAIL_USER          - the mailbox to send FROM and TO, e.g.
                        bilal.magomedov.job@gmail.com
  GMAIL_APP_PASSWORD  - a Gmail App Password for that account (not the
                        normal login password - see README.md)

KEYWORDS and EXCLUDE_KEYWORDS are not secrets - they're hardcoded in
keywords.py, versioned with the rest of the repo. Update that file (not
GitHub secrets) when tuning the match list.

State (which messages were already seen per channel) lives in state.json
next to this script, so the workflow must commit that file back after each
run - it self-heals if a channel disappears from the folder or a new one
is added, no manual bookkeeping needed.
"""
import json
import os
import smtplib
import sys
from email.mime.text import MIMEText
from pathlib import Path

from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import GetDialogFiltersRequest

from keywords import KEYWORDS, EXCLUDE_KEYWORDS

STATE_PATH = Path(__file__).parent / "state.json"
MAX_MESSAGES_PER_CHANNEL_PER_RUN = 100
SNIPPET_LEN = 300


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {}


def save_state(state: dict) -> None:
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def send_email(gmail_user: str, gmail_app_password: str, subject: str, body: str) -> None:
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = gmail_user
    msg["To"] = gmail_user
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_user, gmail_app_password)
        server.sendmail(gmail_user, [gmail_user], msg.as_string())


def _title_text(title) -> str:
    """Folder titles can be plain strings or TextWithEntities depending on
    the Telegram API layer - handle both."""
    if title is None:
        return ""
    if isinstance(title, str):
        return title
    return getattr(title, "text", "") or ""


def get_folder_entities(client: TelegramClient, folder_name: str) -> list:
    """Return the list of resolved chat entities currently inside the
    named Telegram folder. Returns [] if the folder isn't found."""
    result = client(GetDialogFiltersRequest())
    filters = getattr(result, "filters", result)  # some telethon versions return a bare list

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
    keywords = [k.strip().lower() for k in KEYWORDS if k.strip()]
    exclude_keywords = [k.strip().lower() for k in EXCLUDE_KEYWORDS if k.strip()]
    gmail_user = os.environ["GMAIL_USER"]
    gmail_app_password = os.environ["GMAIL_APP_PASSWORD"]

    if not keywords:
        print("No keywords configured, nothing to do.")
        return 0

    state = load_state()
    matches = []  # list of (channel_label, message_id, text, link)

    with TelegramClient(StringSession(session_string), api_id, api_hash) as client:
        entities = get_folder_entities(client, folder_name)
        if not entities:
            print(f"Folder '{folder_name}' not found or empty - nothing to watch this run.")
            return 0

        print(f"Watching {len(entities)} chat(s) in folder '{folder_name}'.")

        for entity in entities:
            channel_key = str(entity.id)
            channel_label = getattr(entity, "title", None) or getattr(entity, "username", None) or channel_key
            last_seen_id = state.get(channel_key, {}).get("last_id")

            new_messages = list(
                client.iter_messages(
                    entity,
                    min_id=last_seen_id or 0,
                    limit=MAX_MESSAGES_PER_CHANNEL_PER_RUN,
                )
            )
            if not new_messages:
                continue

            highest_id = max(m.id for m in new_messages)

            if last_seen_id is None:
                # First time seeing this chat: record the high-water mark
                # but don't alert on the whole backlog.
                state[channel_key] = {"last_id": highest_id, "label": channel_label}
                print(f"{channel_label}: first run, baselined at message {highest_id}, no alerts this time.")
                continue

            for m in new_messages:
                text = (m.message or "").strip()
                if not text:
                    continue
                lower = text.lower()
                if any(kw in lower for kw in keywords) and not any(kw in lower for kw in exclude_keywords):
                    username = getattr(entity, "username", None)
                    link = f"https://t.me/{username}/{m.id}" if username else "(private channel, no link)"
                    snippet = text[:SNIPPET_LEN] + ("..." if len(text) > SNIPPET_LEN else "")
                    matches.append((channel_label, m.id, snippet, link))

            state[channel_key] = {"last_id": highest_id, "label": channel_label}

    save_state(state)

    if matches:
        lines = []
        for channel_label, msg_id, snippet, link in matches:
            lines.append(f"[{channel_label}] {link}\n{snippet}\n")
        body = "\n---\n".join(lines)
        subject = f"[TG-VACANCY] {len(matches)} new match(es) across your watched channels"
        send_email(gmail_user, gmail_app_password, subject, body)
        print(f"Sent digest email with {len(matches)} match(es).")
    else:
        print("No new keyword matches this run.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
