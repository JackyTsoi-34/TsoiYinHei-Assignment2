# Prompt Log — Mini-Assignment 2: Text Statistics Tool

This file contains the complete chat history with the AI assistant used
while designing and implementing this assignment.

---

## Session 1 — Tool Design Brainstorming

**User:**
I need to build a custom tool for an AI agent for my IIMT3688 assignment.
The tool should be useful for business or news text analysis. What are some
good ideas that are simple but demonstrate solid tool design?

**Assistant:**
Here are a few strong candidates that are both practical and well-scoped:

1. **Text Statistics Analyzer** — word count, sentence count, readability
   score, avg word length, top keywords. Pure stdlib, fast, and very useful
   for pre-filtering or profiling text before sending it to an LLM.
2. **Keyword Extractor** — returns the top N keywords by TF-IDF or simple
   frequency, after removing stopwords.
3. **Date Parser/Normalizer** — finds date strings in any format and
   normalizes them to ISO-8601.
4. **Sentiment Heuristic Scorer** — counts positive/negative seed words and
   returns a polarity score.
5. **URL Validator** — checks that URLs in text are structurally valid and
   optionally reachable.

For your assignment a **Text Statistics Analyzer** is the strongest choice
because: (a) it has clear, testable inputs/outputs, (b) it requires no
external libraries, so graders won't have install issues, (c) the readability
score gives it a non-trivial algorithmic element, and (d) it naturally fits
a business/news analysis pipeline.

**User:**
OK, let's go with the Text Statistics Analyzer. What metrics should it return?

**Assistant:**
I'd recommend returning these seven fields in a dict:

- `word_count` — `len(re.findall(r"\b[a-zA-Z']+\b", text))`
- `sentence_count` — split on `[.!?]+`
- `paragraph_count` — split on `\n{2,}`
- `avg_word_length` — mean chars per word
- `avg_sentence_length` — mean words per sentence
- `readability_score` — simplified Flesch Reading Ease:
  `206.835 - 1.015 * (words/sentences) - 84.6 * (avg_word_length / 3)`
  (word length ÷ 3 is used as a syllable proxy to avoid NLTK dependency)
- `top_keywords` — most frequent tokens after removing ~50 stopwords

Return type should be a JSON-serializable dict with `"status": "success"` or
`"status": "error"` as the first field, so agent loops never crash.

---

## Session 2 — Tool Implementation

**User:**
Write me the full `TextStatsTool` class with type hints and error handling.

**Assistant:**
Here's the implementation. Key points:

- Input validation checks: not a string, empty after strip, over 100 000 chars
- `top_n` is validated and clamped to [1, 50]
- All analysis is wrapped in a try/except to catch unexpected failures
- Keywords are returned as `[[word, count], ...]` (lists, not tuples) so the
  result is directly JSON-serializable
- The class is paired with a `Tool` wrapper as suggested in the spec

*(full code as in tool.py)*

**User:**
Should I use `dict[str, Any]` or `Dict[str, Any]` from typing?

**Assistant:**
Use `dict[str, Any]` — built-in generics have been supported since Python 3.9,
and you're on Python 3.14, so there's no reason to import `Dict` from `typing`.
Just keep `from typing import Any` at the top.

---

## Session 3 — Demo Design

**User:**
The demo needs to show the tool being called by an AI agent. I'm required to
use the DeepSeek API. What's the simplest reliable way to do this?

**Assistant:**
DeepSeek's API is OpenAI-compatible, so you can use the `openai` Python package
pointed at DeepSeek's base URL:

```python
from openai import OpenAI
client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"),
                base_url="https://api.deepseek.com")
```

Then define your tool as a standard OpenAI function-calling schema and pass it
as `tools=[...]` to `chat.completions.create`. The model `deepseek-chat`
(DeepSeek-V3) supports function calling. This is more reliable than CrewAI for
a small demo because it has fewer moving parts and no framework-specific quirks.

**User:**
How should the demo show error handling?

**Assistant:**
Run at least two error scenarios directly on the tool (without going through
the LLM, so graders can see the raw structured output) and one scenario through
the agent so it's clear the agent handles tool errors gracefully:

- Direct call with empty/whitespace string → `{"status": "error", ...}`
- Direct call with integer input → `{"status": "error", ...}`
- Agent asked to analyze `''` → receives the error and explains it to user

This covers both unit-level and integration-level error handling.

---

## Session 4 — API Key Handling

**User:**
How should I handle the DeepSeek API key so it's never hardcoded?

**Assistant:**
Two patterns — support both:

1. **Environment variable**: `os.getenv("DEEPSEEK_API_KEY")` with a clear
   `sys.exit()` message if it's missing.
2. **`.env` file**: load with `python-dotenv`'s `load_dotenv()` before the
   `os.getenv` call; fail gracefully if dotenv isn't installed.

Include a `.env.example` file (committed to the repo) with:
```
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```
Add `.env` to `.gitignore` so real keys are never committed.

**User:**
Good. What packages do I need in requirements.txt?

**Assistant:**
Just two:
```
openai>=1.0.0
python-dotenv>=1.0.0
```
The tool itself uses only stdlib, so no NLP packages are needed.

---

## Session 5 — Review and Refinement

**User:**
Can you review the tool.py one more time and check for edge cases I may have
missed?

**Assistant:**
A few things to double-check:

1. `top_n` type coercion — you wrap it in `int()` and catch `TypeError /
   ValueError`, which handles `None`, strings, and floats correctly. ✓
2. Zero-word text — e.g., `"123 456"` has no alphabetic tokens; the word-count
   check catches this and returns a clean error. ✓
3. JSON-serializability of `top_keywords` — using `[[word, count], ...]`
   (list of lists) instead of a list of tuples avoids `json.dumps` failures. ✓
4. `paragraph_count` uses `max(..., 1)` so text without blank lines still
   reports at least one paragraph. ✓
5. Readability clamped to [0, 100] — very long complex sentences could produce
   a negative raw score; the `max(0.0, ...)` guard handles this. ✓

One suggested improvement: strip apostrophes from the stopword-exclusion length
check (`len(w) > 2`) to avoid letting contractions like `"it's"` slip through.
The current code does `len(w) > 2` on the original word before lowercasing,
so `"it"` (len 2) is excluded, but `"it's"` (len 4) could appear. That's
actually fine — contractions are rare in formal business text and the stopword
list already covers `"s"` and `"t"`.

**User:**
Looks good. Write me a final README.md with setup and run instructions.

**Assistant:**
*(full README as in README.md)*

---

*End of prompt log.*
