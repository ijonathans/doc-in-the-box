"""Resolve relative time phrases (e.g. 'yesterday', '2 days ago') to explicit date strings using today's date."""

import re
from datetime import date, timedelta


def resolve_relative_timeline(text: str) -> str | None:
    """
    If text contains a relative time phrase, return an explicit date string (e.g. "February 20, 2025").
    Otherwise return None so callers do not overwrite existing explicit timelines.
    Uses datetime.date.today() and standard library only.
    """
    if not text or not text.strip():
        return None
    t = text.strip().lower()
    today = date.today()

    # yesterday
    if re.search(r"\byesterday\b", t):
        d = today - timedelta(days=1)
        return d.strftime("%B %d, %Y")

    # today
    if re.search(r"\btoday\b", t):
        return today.strftime("%B %d, %Y")

    # X day ago / X days ago
    m = re.search(r"\b(\d+)\s+day(s)?\s+ago\b", t)
    if m:
        n = int(m.group(1))
        d = today - timedelta(days=n)
        return d.strftime("%B %d, %Y")

    # last week / a week ago
    if re.search(r"\b(last\s+week|a\s+week\s+ago)\b", t):
        d = today - timedelta(days=7)
        return d.strftime("%B %d, %Y")

    # X weeks ago
    m = re.search(r"\b(\d+)\s+week(s)?\s+ago\b", t)
    if m:
        n = int(m.group(1))
        d = today - timedelta(weeks=n)
        return d.strftime("%B %d, %Y")

    # last month / a month ago (approximate)
    if re.search(r"\b(last\s+month|a\s+month\s+ago)\b", t):
        d = today - timedelta(days=30)
        return d.strftime("%B %d, %Y")

    # X months ago
    m = re.search(r"\b(\d+)\s+month(s)?\s+ago\b", t)
    if m:
        n = int(m.group(1))
        d = today - timedelta(days=30 * n)
        return d.strftime("%B %d, %Y")

    return None
