"""
Hardcoded keyword configuration for the vacancy watcher.

Update this file (not GitHub secrets) whenever a new channel is added to
the Telegram folder, or when a match quality issue shows up. Workflow:
pull the last few posts from the new channel, look at their format and
wording, then add/remove entries here and note why under CHANNEL_NOTES.

KEYWORDS  - a message must contain at least one of these (case-insensitive
            substring match) to be considered a candidate match.
EXCLUDE_KEYWORDS - a message matching KEYWORDS is skipped if it also
            contains any of these (case-insensitive substring match).
            Used to filter out resume/candidate posts that happen to
            contain a role keyword.
"""

KEYWORDS = [
    "project manager",
    "programme manager",
    "program manager",
    "pmo",
    "project management",
    "project lead",
    "technical project manager",
    "it project manager",
    "delivery manager",
    "менеджер проекта",
    "менеджер проектов",
    "руководитель проекта",
    "руководитель проектов",
]

EXCLUDE_KEYWORDS = [
    "резюме",
    "ищу работу",
    "ищу позицию",
    "ищу вакансию",
    "рассматриваю предложения",
    "меня зовут",
    "candidate",
    "cv",
    "resume",
    "opentowork",
    "open to work",
]

# Per-channel notes: format observed and why keywords were tuned when the
# channel was added or reviewed. Add an entry here every time.
CHANNEL_NOTES = {
    "CY iT HR": (
        "Смешанный канал: резюме и вакансии вперемешку. Почти каждый пост "
        "размечен хэштегами: #CV/#resume/#резюме/#opentowork для резюме, "
        "#vacancy/#вакансия для вакансий. 'remote' как ключевое слово сам "
        "по себе слишком общий - ловит вакансии любых профессий."
    ),
    "Projects Jobs — вакансии и аналитика": (
        "В основном резюме кандидатов на PM/PgM-позиции. Не все посты "
        "помечены хэштегами, но почти все резюме начинаются с 'Меня зовут' "
        "или содержат контакты (Telegram/Email/Телефон) кандидата."
    ),
}
