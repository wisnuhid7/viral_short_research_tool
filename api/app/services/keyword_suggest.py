"""Keyword suggestion extraction from search-result videos.

Port of server/src/services/keyword-suggest.ts.
"""
import re

from api.app.db.queries import get_keyword_suggestions, save_keyword_suggestions
from api.app.logger import info as log_info

# ─── Stop words (common Indonesian + English) ────────────

STOP_WORDS: set[str] = {
    # English
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "this", "that", "these",
    "those", "i", "you", "he", "she", "it", "we", "they", "me", "him",
    "her", "us", "them", "my", "your", "his", "its", "our", "their",
    "what", "which", "who", "whom", "where", "when", "why", "how",
    "not", "no", "nor", "but", "and", "or", "if", "then", "else",
    "for", "of", "to", "in", "on", "at", "by", "with", "from", "up",
    "about", "into", "over", "after", "so", "than", "too", "very",
    # Indonesian
    "yang", "dan", "di", "ke", "dari", "ini", "itu", "untuk", "dengan",
    "pada", "adalah", "akan", "sudah", "juga", "atau", "ada", "tidak",
    "bisa", "saya", "kamu", "dia", "kami", "mereka", "satu", "dua",
    "tiga", "nya", "lagi", "baru", "jadi", "aja", "gak", "ga", "ya",
    "nih", "dong", "sih", "loh", "deh", "kan", "banget",
    # Common in titles
    "shorts", "short", "video", "part",
}

# JS `\w` is ASCII-only; Python `\w` is Unicode-aware, so use an explicit class.
_NON_WORD_SPACE = re.compile(r"[^A-Za-z0-9_\s]")


def extract_keyword_suggestions(parent_keyword: str, videos: list[dict]) -> list[dict]:
    """Extract keyword suggestions from search-result videos.

    Sources: video tags and frequently-occurring title words.
    """
    tag_frequency: dict[str, int] = {}
    title_word_frequency: dict[str, int] = {}
    parent_lower = parent_keyword.lower()

    for video in videos:
        # Tags
        for tag in video["tags"]:
            normalized = tag.lower().strip()
            if len(normalized) > 1 and normalized != parent_lower and normalized not in STOP_WORDS:
                tag_frequency[normalized] = tag_frequency.get(normalized, 0) + 1

        # Title words (3+ character words, not stop words)
        words = [
            w
            for w in _NON_WORD_SPACE.sub(" ", video["title"].lower()).split()
            if len(w) > 2 and w not in STOP_WORDS and w != parent_lower
        ]

        for word in words:
            title_word_frequency[word] = title_word_frequency.get(word, 0) + 1

    suggestions: list[dict] = []

    # Tags with frequency ≥ 2
    for keyword, freq in tag_frequency.items():
        if freq >= 2:
            suggestions.append(
                {"keyword": keyword, "source": "tag", "frequency": freq, "parentKeyword": parent_lower}
            )

    # Title words with frequency ≥ 3
    for keyword, freq in title_word_frequency.items():
        if freq >= 3:
            suggestions.append(
                {"keyword": keyword, "source": "title_word", "frequency": freq, "parentKeyword": parent_lower}
            )

    # Sort by frequency descending (stable, like JS Array.sort), limit to top 30
    suggestions.sort(key=lambda s: -s["frequency"])
    top = suggestions[:30]

    # Persist to DB
    if len(top) > 0:
        save_keyword_suggestions(top)
        log_info("Keyword suggestions saved", {"parentKeyword": parent_keyword, "count": len(top)})

    return top


def get_cached_keyword_suggestions(parent_keyword: str) -> list[dict]:
    """Get cached keyword suggestions from DB."""
    return get_keyword_suggestions(parent_keyword)
