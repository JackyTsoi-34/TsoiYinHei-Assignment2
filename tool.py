"""
tool.py — Text Statistics Tool for AI Agent Integration

This module implements a text analysis tool designed for use with AI agents.
It provides word count, readability metrics, sentence statistics, and keyword
extraction from plain text — useful for business and news article analysis.

No external packages required: only the Python standard library is used.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any


# ---------------------------------------------------------------------------
# Core analysis class
# ---------------------------------------------------------------------------


class TextStatsTool:
    """
    Analyzes a piece of text and returns statistical metrics.

    The tool is intentionally dependency-free (stdlib only) so it is fast,
    portable, and easy to integrate into any agent framework.
    """

    # ~50 common English stopwords excluded from keyword extraction
    _STOPWORDS: frozenset[str] = frozenset(
        {
            "a", "an", "the", "and", "or", "but", "in", "on", "at", "to",
            "for", "of", "with", "by", "from", "is", "was", "are", "were",
            "be", "been", "has", "have", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "can", "shall", "it",
            "its", "this", "that", "these", "those", "i", "we", "you", "he",
            "she", "they", "them", "their", "our", "your", "his", "her", "as",
            "not", "no", "so", "if", "then", "than", "also", "just", "up",
            "about", "into", "which", "who", "what", "when", "where", "how",
            "all", "each", "some", "any", "more", "most", "other", "such",
            "s", "t", "re", "ve", "ll", "d", "m",
        }
    )

    def run(self, text: str, top_n: int = 10) -> dict[str, Any]:
        """
        Analyze *text* and return a dictionary of statistics.

        Parameters
        ----------
        text : str
            The text to analyze. Must be a non-empty string of at most
            100 000 characters.
        top_n : int, optional
            How many top keywords to return (clamped to [1, 50]).
            Defaults to 10.

        Returns
        -------
        dict
            On success::

                {
                    "status": "success",
                    "word_count": int,
                    "sentence_count": int,
                    "paragraph_count": int,
                    "avg_word_length": float,
                    "avg_sentence_length": float,
                    "readability_score": float,   # 0-100, higher = easier
                    "top_keywords": [[word, count], ...]
                }

            On any error::

                {"status": "error", "error": "<human-readable message>"}
        """
        # ── Input validation ───────────────────────────────────────────────
        if not isinstance(text, str):
            return {
                "status": "error",
                "error": f"Expected a string, got {type(text).__name__!r}.",
            }

        text = text.strip()
        if not text:
            return {"status": "error", "error": "Input text cannot be empty."}

        if len(text) > 100_000:
            return {
                "status": "error",
                "error": "Text is too long (max 100 000 characters).",
            }

        try:
            top_n = int(top_n)
        except (TypeError, ValueError):
            top_n = 10
        top_n = max(1, min(top_n, 50))

        # ── Analysis ───────────────────────────────────────────────────────
        try:
            # Words: sequences of letters and apostrophes
            words = re.findall(r"\b[a-zA-Z']+\b", text)
            word_count = len(words)
            if word_count == 0:
                return {
                    "status": "error",
                    "error": "No alphabetic words found in the input text.",
                }

            # Sentences split on . ! ?
            raw_sentences = re.split(r"[.!?]+", text)
            sentences = [s.strip() for s in raw_sentences if s.strip()]
            sentence_count = max(len(sentences), 1)

            # Paragraphs separated by one or more blank lines
            raw_paragraphs = re.split(r"\n{2,}", text)
            paragraph_count = max(
                len([p for p in raw_paragraphs if p.strip()]), 1
            )

            avg_word_length = round(
                sum(len(w) for w in words) / word_count, 2
            )
            avg_sentence_length = round(word_count / sentence_count, 2)

            # Readability — simplified Flesch Reading Ease.
            # Uses avg word length ÷ 3 as a rough syllable-count proxy,
            # avoiding the need for a syllable-counting library.
            syllable_proxy = avg_word_length / 3.0
            raw_score = (
                206.835
                - 1.015 * avg_sentence_length
                - 84.6 * syllable_proxy
            )
            readability_score = round(max(0.0, min(100.0, raw_score)), 2)

            # Top keywords: frequency of non-stopword tokens (lowercased,
            # length > 2 after stripping apostrophes from the check)
            kw_tokens = [
                w.lower()
                for w in words
                if w.lower() not in self._STOPWORDS and len(w) > 2
            ]
            top_keywords = [
                [word, count]
                for word, count in Counter(kw_tokens).most_common(top_n)
            ]

            return {
                "status": "success",
                "word_count": word_count,
                "sentence_count": sentence_count,
                "paragraph_count": paragraph_count,
                "avg_word_length": avg_word_length,
                "avg_sentence_length": avg_sentence_length,
                "readability_score": readability_score,
                "top_keywords": top_keywords,
            }

        except Exception as exc:  # pragma: no cover — unexpected failures
            return {"status": "error", "error": f"Analysis failed: {exc}"}


# ---------------------------------------------------------------------------
# Generic wrapper  (matches the suggested structure in the assignment spec)
# ---------------------------------------------------------------------------


class Tool:
    """
    Generic tool wrapper that pairs a name and description with a callable.

    This is the structure suggested in the assignment specification.

    Example
    -------
    >>> t = Tool("double", "Doubles a number", lambda x: x * 2)
    >>> t.execute(x=5)
    10
    """

    def __init__(self, name: str, description: str, fn) -> None:
        self.name = name
        self.description = description
        self.fn = fn

    def execute(self, **kwargs) -> Any:
        """Invoke the underlying callable with keyword arguments."""
        return self.fn(**kwargs)


# ---------------------------------------------------------------------------
# Module-level ready-to-use instance
# ---------------------------------------------------------------------------

_analyzer = TextStatsTool()

text_stats_tool = Tool(
    name="text_statistics",
    description=(
        "Analyzes a piece of text and returns statistical metrics including "
        "word count, sentence count, paragraph count, average word length, "
        "average sentence length, a readability score (0–100, higher = easier "
        "to read), and the top keywords by frequency. "
        "Useful for profiling business reports, news articles, or any prose. "
        "Returns a JSON-serializable dict with a 'status' key ('success' or "
        "'error')."
    ),
    fn=_analyzer.run,
)
