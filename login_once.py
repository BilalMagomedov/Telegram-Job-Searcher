"""
Run this ONCE, on your own computer, to log the spare Telegram number in and
produce a StringSession. This is the only step where the phone number, login
code, and 2FA password are ever touched - and they never leave your machine.

Usage:
    pip install telethon
    python login_once.py

You will be asked for:
  - api_id and api_hash (get these for free at https://my.telegram.org
    -> API development tools -> create an app, using the SPARE number)
  - the spare number's phone number (international format, e.g. +9055...)
  - the login code Telegram sends to that number
  - the 2FA password, only if that account has one set

At the end it prints a long string called the "session string". Copy the
WHOLE thing (it's one long line) and save it as the GitHub secret TG_SESSION
described in README.md. Treat it like a password - anyone who has it can log
in as that Telegram account without needing the phone again.
"""
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

def main():
    api_id = int(input("api_id: ").strip())
    api_hash = input("api_hash: ").strip()

    with TelegramClient(StringSession(), api_id, api_hash) as client:
        print("\nLogging in... check the spare number for the code.\n")
        session_string = client.session.save()
        print("\n" + "=" * 60)
        print("COPY EVERYTHING BETWEEN THE LINES BELOW - save it as TG_SESSION")
        print("=" * 60)
        print(session_string)
        print("=" * 60)

if __name__ == "__main__":
    main()
