# Mini-Assignment 2 — Text Statistics Tool

A custom tool for AI agent integration that analyzes plain text and returns
statistical metrics useful for business and news analysis.

---

## What the Tool Does

`text_statistics` (defined in `tool.py`) accepts a text string and returns:

| Metric | Description |
|---|---|
| `word_count` | Total number of words |
| `sentence_count` | Number of sentences |
| `paragraph_count` | Number of paragraphs |
| `avg_word_length` | Mean character count per word |
| `avg_sentence_length` | Mean words per sentence |
| `readability_score` | 0–100 (higher = easier to read; Flesch-based heuristic) |
| `top_keywords` | Most frequent content words (stopwords excluded) |

All outputs are JSON-serializable. Invalid inputs (empty string, wrong type,
text too long) return a structured `{"status": "error", "error": "..."}` dict
rather than raising exceptions.

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Provide your DeepSeek API key

**Option A — environment variable (recommended)**

```bash
# Linux / macOS
export DEEPSEEK_API_KEY=your_key_here
python demo.py

# Windows PowerShell
$env:DEEPSEEK_API_KEY="your_key_here"
python demo.py
```

**Option B — .env file**

```bash
cp .env.example .env
# Open .env and set:  DEEPSEEK_API_KEY=your_key_here
python demo.py
```

---

## Agent & Workflow Design

This project uses a **single-agent, single-tool** design — the minimum needed
to satisfy the integration requirement cleanly.

| Component | Description |
|---|---|
| **Agent** | DeepSeek LLM (`deepseek-chat`) acting as a text-analysis assistant |
| **Tool** | `text_statistics` — analyzes text and returns structured metrics |
| **Integration method** | OpenAI-compatible function calling (tool schema passed to the API) |

The agent decides when to call the tool, executes it with the right arguments,
receives the JSON result, and produces a human-readable summary — all in one
automated loop. No manual orchestration is needed.

> **Note:** The assignment tips mention "3 agents, 3 tasks" as a suggestion for
> CrewAI-style projects. This assignment only requires designing and integrating
> **one custom tool**, which this project fulfils with a focused single-agent
> approach.

---

## Running the Demo

```bash
python demo.py
```

The demo runs five scenarios in sequence:

1. **Agent → tool (news article)** — the DeepSeek agent receives a business
   news excerpt, calls `text_statistics` via function calling, and presents a
   human-readable summary of the results.
2. **Direct tool call (short text)** — `text_stats_tool.execute()` is called
   directly on a short sentence; top 5 keywords are returned.
3. **Error: empty input** — empty string passed; tool returns structured error.
4. **Error: wrong type** — integer passed instead of string; structured error.
5. **Agent handles error** — agent asks to analyze an empty string; it receives
   the error from the tool and gracefully explains the problem to the user.

---

## File Structure

```
A2/
├── tool.py           # TextStatsTool class + generic Tool wrapper
├── demo.py           # Integration demo (DeepSeek API, function calling)
├── README.md         # This file
├── prompt-log.md     # AI-assisted development chat history
├── requirements.txt  # Python dependencies
└── .env.example      # API key variable template
```

---

## Design Decisions

- **Standard-library only for the core tool** — `re` and `collections` are
  sufficient; no NLTK, spaCy, or other heavy NLP packages required.
- **Heuristic readability score** — a simplified Flesch Reading Ease formula
  is used, with average word length serving as a syllable-count proxy. This
  avoids an external syllable-counting dependency while still yielding a
  meaningful signal.
- **Structured errors, not exceptions** — the tool wraps all error paths in
  `{"status": "error", "error": "..."}` so agent loops never crash on bad
  input.
- **JSON-serializable output** — all values are plain Python dicts, lists,
  ints, and floats, making results directly usable as LLM tool responses.
- **Small embedded stopword list** — ~50 common English words are filtered
  from keyword extraction, avoiding a corpus dependency (e.g., NLTK stopwords).

## Limitations

- Readability score is approximate; a precise Flesch score requires real
  syllable counting.
- English-only design; non-Latin scripts will produce low word counts.
- Keyword extraction is frequency-based, not semantic (no TF-IDF or NER).
