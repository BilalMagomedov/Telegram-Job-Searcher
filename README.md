# Telegram-Job-Searcher

Watches the channels inside a Telegram folder (default: "Vacancies") for
messages matching a keyword list, and emails a digest of matches via Gmail
SMTP. Runs every 20 minutes for free on GitHub Actions - no server needed.

The channel list is never hardcoded: it's read fresh from the Telegram
folder on every run, so adding a channel to that folder from your phone is
the entire setup for a new source.

## One-time setup

### 1. Get Telegram API credentials

Go to https://my.telegram.org, log in with the Telegram number you want the
watcher to use, open "API development tools", and create an app. This gives
you an `api_id` and `api_hash`.

### 2. Produce a session string (run locally, once)

This step touches your phone number, login code, and 2FA password, so it
must be run on your own machine - none of that reaches this repo or GitHub.

```
python -m venv .venv
source .venv/bin/activate        # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
python login_once.py
```

Enter your `api_id`, `api_hash`, phone number, the login code Telegram
sends you, and your 2FA password if you have one set. At the end it prints
a long "session string" - copy it, you'll need it for the `TG_SESSION`
secret below. Treat it like a password: anyone with it can log in as that
Telegram account without the phone.

### 3. Set GitHub Actions repository secrets

In this repo: Settings -> Secrets and variables -> Actions -> New
repository secret (or `gh secret set <NAME>` if you have the GitHub CLI
locally). Set:

| Secret | Value |
|---|---|
| `TG_API_ID` | from step 1 |
| `TG_API_HASH` | from step 1 |
| `TG_SESSION` | the string printed by `login_once.py` in step 2 |
| `FOLDER_NAME` | name of the Telegram folder to watch (optional, defaults to `Vacancies`) |
| `GMAIL_USER` | the Gmail address to send/receive digests, e.g. `bilal.magomedov.job@gmail.com` |
| `GMAIL_APP_PASSWORD` | a Gmail App Password for that account (not the normal login password) - turn on 2-Step Verification at https://myaccount.google.com/security, then generate one at https://myaccount.google.com/apppasswords |

`KEYWORDS` and `EXCLUDE_KEYWORDS` are NOT secrets - see the next section.

### 4. Match keywords (hardcoded in `keywords.py`, not a secret)

`KEYWORDS` (a message must contain at least one) and `EXCLUDE_KEYWORDS` (a
matching message is dropped if it also contains one of these, used to
filter out resume/candidate posts) live in `keywords.py` at the repo root,
versioned like any other code.

**When you add a new channel to the Telegram folder:** pull its last few
posts, look at the wording and any hashtags it uses, and update
`keywords.py` accordingly - add role synonyms that channel uses to
`KEYWORDS`, add any resume/candidate markers specific to it to
`EXCLUDE_KEYWORDS`, and note the reasoning under `CHANNEL_NOTES` in that
file. Commit and push; the next scheduled run picks it up automatically.

### 5. Run it

The workflow (`.github/workflows/watch.yml`) runs automatically every 20
minutes. You can also trigger it manually from the Actions tab, or with
`gh workflow run watch.yml`. Matches arrive by email with the subject tag
`[TG-VACANCY]`. `state.json` tracks which messages were already seen per
channel and is committed back by the workflow after each run.

There's also a one-off `.github/workflows/backfill.yml` (input: a UTC date)
to scan a specific past day with the current `keywords.py` filters, useful
when checking whether a keyword change would have caught/excluded the
right posts. It doesn't touch `state.json` or the regular schedule.