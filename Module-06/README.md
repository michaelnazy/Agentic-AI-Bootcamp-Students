# Module 6 — Memory Systems & Context Engineering

> **The one thing to leave with:** memory is what you *store*. Context is what you
> *show* the model. They are two different decisions, and the second one has a
> price on it.

Last session a skill with 192 rules loaded five of them, and that was the whole
point. Today your agent gets a past — a folder on disk that survives a restart —
and then you learn why showing it *less* of that past is usually the better
answer.

---

## Read this before you touch anything

### 1. Use the right Python

Same environment as Modules 1–5. **Python 3.12.** Not 3.14 — chromadb has no
wheels for it yet and `pip` will fail after a long silence.

```powershell
Module-02\.venv\Scripts\python.exe --version      # expect 3.12.x
```

### 2. Install

```powershell
Module-02\.venv\Scripts\python.exe -m pip install -r Module-06\requirements.txt
```

Four packages. `chromadb` brings its own embedding model — **no torch, no
second API key**. It downloads once (~80 MB) the first time you store anything.

### 3. Your `.env`

`OPENROUTER_API_KEY` at the repo root. Same one as always.

### 4. Setup check — do this the day before

```powershell
Module-02\.venv\Scripts\python.exe Module-06\m6_preflight.py
```

If every line says `[ OK ]` you are ready. This run also triggers the one-time
model download, so it does not happen on classroom wifi during the lab.

---

## The module, in order

| # | folder | what you do | time |
|---|---|---|---|
| 1 | **`demos/`** | Four demos, four numbers. Watch, then read the source — each is under 120 lines. | 45 min |
| 2 | **`starter-code/`** | The lab: build the Personal Knowledge Assistant. Short-term, then long-term. | 1 h 50 |
| 3 | **`exercise/`** | Context engineering, measured: select, compress, order — and a number for each. | 30 min |
| — | `M6-Whiteboard.html` | Open in a browser. The concept blocks, click to advance. | — |

**Every folder has its own README or worksheet. That file is your instructions.**

Also here:

- `M6-Learner-Handout.md` — the concepts, written down. Sections 1–5.
- `M6-Lab-Worksheet.md` — the lab, step by step, with checkpoints.
- `exercise/EXERCISE.md` — Part 3, and the template for the memory-policy note you submit.

---

## The four-hour shape

| time | what |
|---|---|
| 0:00 – 0:10 | Review: the M5B bridge PRs, and the number from demo 4 — 192 rules, 5 loaded |
| 0:10 – 0:30 | Two memories, two timescales — whiteboard boards 1–8 |
| 0:30 – 1:15 | **Part 1** · four demos with numbers (`demos/`) |
| 1:15 – 1:25 | break |
| 1:25 – 3:15 | **Part 2** · the lab — short-term (45) then long-term (65) (`starter-code/`) |
| 3:15 – 3:45 | **Part 3** · context engineering, measured (`exercise/`) — boards 9–12 open it |
| 3:45 – 3:55 | showcase — one number each: prompt size before, after, and which lever |
| 3:55 – 4:00 | closing + quiz |

---

## What you hand in

Completes the Phase 3 mini-project. Handout §7 has the detail.

1. `memory_agent.py` — short-term summarisation + persistent long-term memory with citations.
2. **Cross-restart evidence** — the two runs, two processes, the second one recalling the first.
3. **The memory-policy note** (½ page) — write / summarise / evict, plus one
   context-engineering lever with its measured saving. `exercise/EXERCISE.md` has the template.

---

## When something breaks

| symptom | cause | fix |
|---|---|---|
| `ModuleNotFoundError: chromadb` | wrong interpreter | `Module-02\.venv\Scripts\python.exe`, not `python` |
| the first `add()` hangs for a minute | one-time model download | wait; or run `m6_preflight.py` the day before like it says |
| "No recall after restart" | `DB_DIR` was relative to the folder you ran from — or run 2 was in the same process | anchor it to `__file__` (the starter does); run 2 must be a new process |
| distances above 1, negative "similarities" | collection created without `hnsw:space: cosine` | delete `memory_store/` and recreate — the space is fixed at creation |
| `attempt to write a readonly database` | you deleted the store while a client had it open | exit, delete, start again; wipe *before* opening |
| `â€"` in the terminal | Windows cp1252 console | the `sys.stdout.reconfigure` block at the top of every script here |
| `404 ... no endpoints` | model unavailable on this account | `$env:MODEL="openai/gpt-4.1-mini"` |
| it remembers junk | write policy too loose | store durable preferences and facts, not questions or answers |
| it cites nothing | the system prompt asks *if relevant* | tell it to *apply* preferences and cite what it applied |

---

## What we are *not* doing today

We are not building a knowledge graph, we are not installing a memory framework
(mem0, LangMem, Zep), and we are not fine-tuning a re-ranker. All three are
real. All three are an afternoon once you have written the write / summarise /
evict policies yourself and *measured* what select, compress and order do to the
bill — which is what today is.

Memory is a folder and three policies. Get those right and the framework is a
detail.
