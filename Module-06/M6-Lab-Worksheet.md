<!-- JHF-BRAND -->
<div align="center" style="padding:28px 20px; background:#ffffff; border:2px solid #e0e0e0; border-radius:12px;">
  <p style="margin:0 0 16px 0;">
    <img src="../assets/jhf-logo.png" alt="Jerusalem High-Tech Foundry (JHF)" height="54" style="vertical-align:middle; margin:0 22px;" />
    <img src="../assets/comcec-logo.png" alt="COMCEC - Cooperation for Development" height="72" style="vertical-align:middle; margin:0 22px;" />
  </p>
  <h1 style="color:#1a3c5e; margin:6px 0;">Agentic AI Bootcamp</h1>
  <h3 style="color:#0078d4; margin:4px 0; font-weight:600;">Module 6 &middot; Lab Worksheet &mdash; Personal Knowledge Assistant</h3>
  <hr style="border:0; border-top:1px solid #0078d4; width:60%; margin:16px auto;" />
  <p style="font-size:14px; color:#555; margin:6px 0;">
    <strong>Lead Trainer</strong><br/>
    <a href="https://www.linkedin.com/in/alaaldin-ahmed-260266150" target="_blank">Alaaldin Ahmed</a>
  </p>
  <p style="font-size:12.5px; color:#777; margin:8px 0 0 0;">
    Organized by <strong>Jerusalem High-Tech Foundry (JHF)</strong> &nbsp;&middot;&nbsp; In partnership with <strong>COMCEC</strong>
  </p>
</div>

# Module 6 — Lab Worksheet
## Build the Personal Knowledge Assistant (Memory)

> **Time:** ~45 min (Part 1) + ~65 min (Part 2) + ~30 min (Part 3, in `exercise/`)
> **Files:** copy `starter-code/memory_agent_starter.py` → `memory_agent.py` (same folder)
> **Goal:** an assistant with **short-term** (summarised) and **long-term** (persistent vector)
> memory that recalls across restarts and cites what it recalled.
> Use GitHub Copilot for boilerplate; understand the write path and the read path yourself.

> **The one thing to leave with:** memory is what you store. Context is what you show the model.

---

## Definition of done

Two commands. **Two processes.** The second one has never seen the first sentence.

```powershell
..\.venv\Scripts\python.exe memory_agent.py --run1     # "I prefer metric units and I'm researching renewable energy."
..\.venv\Scripts\python.exe memory_agent.py --run2     # "Give me a quick figure for solar capacity."
```

Run 2 **retrieves** the two memories from disk, answers in **metric**, and **cites** the
memory it used — `(from your stored preference, 2026-09-18)`. The context sent to the model
stays bounded however long you keep talking.

---

## Setup gate (5 min)

Module 6 has **its own virtual environment**, inside `Module-06\.venv`. Everything in this
worksheet is run from `Module-06\starter-code`, so the interpreter is always `..\.venv`.

If you did not create it the day before, do it now (Python **3.12**, not 3.14):

```powershell
cd Module-06
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

```bash
# macOS / Linux
cd Module-06
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Then confirm:

```powershell
.venv\Scripts\python.exe m6_preflight.py        # from Module-06
```

- ✅ every line `[ OK ]` (two `[WARN]` on versions is fine) → go.
- ❌ `chromadb CANNOT install on 3.14` → you are on the wrong interpreter. Recreate `.venv` with 3.12.
- ❌ `.env: OPENROUTER_API_KEY missing` → it lives at the **repo root**, same as M1–M5.

Then copy the starter, and run it once as it is:

```powershell
cd starter-code
copy memory_agent_starter.py memory_agent.py
..\.venv\Scripts\python.exe memory_agent.py --run1
```

```bash
# macOS / Linux
cd starter-code
cp memory_agent_starter.py memory_agent.py
../.venv/bin/python memory_agent.py --run1
```

> From here on, every `python` in this worksheet means `..\.venv\Scripts\python.exe`
> (Windows) or `../.venv/bin/python` (macOS / Linux), run from `Module-06\starter-code`.
> Do not use the bare `python` on your PATH — that is how you end up on 3.14.

🧪 **Checkpoint.** It prints the store path, then dies with `NotImplementedError` in
`ShortTermMemory.add`. Not `ImportError`, not `KeyError`. If it is either of those, fix it now.

Uncomment the `llm`, `client` and `collection` lines at the top. Read the comment next to
`get_or_create_collection` — **cosine** — before you move on.

---

## PART 1 — Short-term memory + summarisation (Steps 1–5 · 45 min)

Context: whiteboard boards 3–4, handout §1.

### Step 1 — Conversation buffer

`ShortTermMemory.add()` already appends. Make `context()` return the buffer as one string
(`role: text`, one per line). Make `answer()` do the minimum: build `[system, ...buffer, question]`,
call the LLM, print a one-line receipt with the prompt size from `resp.usage_metadata["input_tokens"]`,
then `stm.add()` both the question and the answer.

🧪 **Checkpoint.** `--chat`, three turns. The receipt's prompt size goes **up every turn**. That is
the M1 problem, on your screen.

### Step 2 — The trigger

Pick one: `len(self.buffer) > SUMMARIZE_AFTER_TURNS` (turns), or a token count via `tiktoken`
(budget). Turns is simpler; a budget gives a flatter line. Either is correct — say which in your note.

🧪 **Checkpoint.** Print `[trigger fired]` when it would fire. In `--chat`, it fires on the **7th**
message with the defaults (six turns = three exchanges).

### Step 3 — The summarise node

When the trigger fires: take `self.buffer[:-KEEP_LAST]`, fold them into `self.summary` with **one**
LLM call ("update the running summary; keep durable facts and open questions; max 80 words"), and
keep only the last `KEEP_LAST` turns verbatim.

🧪 **Checkpoint.** Print the summary when it is made. After the fold, `len(self.buffer)` is 4 and
`self.summary` is a paragraph, not a transcript.

### Step 4 — Bounded context

`context()` now returns `SUMMARY: ... \n RECENT: ...`. `answer()` sends the summary as a system
message and the recent turns as real `user` / `assistant` messages.

🧪 **Checkpoint.** Ten turns in `--chat`. The prompt size climbs, drops at the fold, climbs, drops.
Write down turn 4 and turn 10. **The line is a sawtooth, not a ramp.**

### Step 5 — Part 1 done

🧪 **Checkpoint.** Hold an 8-turn conversation. Summarisation fires at least once, the context stops
growing without bound, and the assistant can still answer a question about something you said in
turn 1 — from the summary.

> ✅ **End of Part 1:** short-term memory that will not blow up your context. Kill the process.
> Start it again. Ask what you were talking about. **It has no idea.** That is Part 2.

---

## PART 2 — Long-term persistent vector memory (Steps 6–9 · 65 min)

Context: whiteboard boards 5–8, handout §2–§4.

### Step 6 — The write policy, then the write path

Two functions. **The policy first**: `should_remember(text)` returns a memory type
(`"preference"`, `"fact"`) or `None`. A handful of regexes is enough — *I prefer*, *I like*,
*I'm researching*, *my project*. Everything else returns `None`. Split on `;` and on ` and I` so the
run-1 sentence becomes **two** memories.

Then the path: `write_memory(text, mem_type)` → `collection.upsert(ids=[...], documents=[text],
metadatas=[{...}])` with **all four**: `text`, `source`, `timestamp` (today's date, for the citation),
`type`. Add `ts` (epoch seconds) too — you will want it for the stretch. Use a hash of the text as the
id so re-running `--run1` does not duplicate.

🧪 **Checkpoint.** `--run1`. Two `[stored ...]` lines. The folder `memory_store/` now exists
**next to your script** — `dir` it. If it appeared somewhere else, your `DB_DIR` is relative to the
wrong thing.

### Step 7 — The read path

`recall(query, k)` → `collection.query(query_texts=[query], n_results=k,
include=["documents", "metadatas", "distances"])`. Return a list of dicts with the text, type,
timestamp and `similarity = 1 - distance`. Drop anything under `0.2`.

In `answer()`, put the recalled memories in a system message **after the rules and before the
summary**, numbered, each with its type and date.

🧪 **Checkpoint.** Print the recalled memories with their similarity. For run 2's question,
*"I'm researching renewable energy"* comes back around 0.4 and *"I prefer metric units"* around 0.25.
Both above the floor, both below the near-miss zone you saw in demo 3.

### Step 8 — Persistence across a restart ⭐ the checkpoint

```powershell
..\.venv\Scripts\python.exe memory_agent.py --run1
..\.venv\Scripts\python.exe memory_agent.py --run2      # a NEW process
```

🧪 **Checkpoint.** Run 2's first line says `memories on disk: 2` **before** you have said anything.
Its receipt says `recalled: 2`. If it says 0: same folder? Same `DB_DIR`? Did you run 2 in the same
process by accident? (Then you have proved nothing — the buffer did the work.)

### Step 9 — Cite what you used

Tell the model, in the system prompt: *treat every preference in RECALLED MEMORIES as an instruction;
cite each memory you apply, exactly as `(from your stored <type>, <date>)`.* Do not say *if
relevant* — the model will decide nothing is.

🧪 **Final checkpoint.** The full definition of done, end to end, across a restart: metric units,
a citation with today's date, and a bounded context. **Screenshot both terminals.** That is
deliverable 2.

> ✅ **End of Part 2.** Your agent has a past. Now to Part 3 — where you learn to show it less of it.

---

## PART 3 — Context engineering, measured (30 min)

**→ `exercise/EXERCISE.md`.** Same memories, same question, four ways of building the context, and
a number for each. It ends with the template for the memory-policy note you submit.

---

## Showcase (10 min)

One number each, from the exercise table: **prompt size before, prompt size after, and which lever.**
No slides. Terminal, or the receipt pasted into chat.

---

## Stretch goals (if you finish early)

- **Forget / decay.** `forget(older_than_days, mem_type="episodic")` — delete episodic memories
  past a TTL (`collection.delete(where={"$and": [{"type": "episodic"}, {"ts": {"$lt": cutoff}}]})`),
  or re-score by `sim × 0.5^(age/half_life)` like demo 4. Show a stale memory losing.
- **Metadata filter.** `recall(query, mem_type="preference")` via `where={"type": ...}` — cheaper
  than embed-then-filter, and it never returns an episode by mistake.
- **A token budget instead of a turn count** for the summarise trigger. Compare the curve.
- **An LLM write policy.** Replace the regexes with one cheap call that returns
  `preference | fact | none`. Which one stores more junk?

---

## Deliverables (completes the Phase 3 mini-project)

1. `memory_agent.py` — short-term summarisation + persistent long-term memory with citation.
2. **Cross-restart evidence** — screenshots or logs of run 1 and run 2 in two processes.
3. **The memory-policy note** (½ page) — write / summarise / evict, plus one context-engineering
   lever with its measured saving. Template at the end of `exercise/EXERCISE.md`.

`solution-code/memory_agent_solution.py` is released after the session. Compare **after** yours works.

---

## Self-grade before you submit

| # | Criterion | You pass when |
|:-:|---|---|
| 1 | Bounded | A 10-turn chat shows the prompt size drop at least once, and you can say why |
| 2 | Survives a restart | Run 2, in a **new process**, says `memories on disk: 2` before you type anything |
| 3 | Policy, not dump | `should_remember()` says **no** to run 2's question — you can show the `None` |
| 4 | Cites | The run-2 answer contains `(from your stored preference, <today>)` |
| 5 | Measured | The policy note names one lever and a percentage from **your** exercise run |

4 of 5 = PASS.

---

## Troubleshooting

| symptom | cause | fix |
|---|---|---|
| `ModuleNotFoundError: chromadb` | wrong interpreter | `..\.venv\Scripts\python.exe` from `starter-code`, not bare `python` |
| `NotImplementedError` | expected — that is your next TODO | read the step number in the comment |
| the first `upsert` hangs ~15 s | chromadb downloading its embedding model | one-time; you skipped `m6_preflight.py` |
| no recall after restart | `DB_DIR` relative to the folder you ran from; or run 2 in the same process | `Path(__file__).parent / "memory_store"` (the starter does this: the store is `Module-06\starter-code\memory_store`); a new process |
| distances > 1, similarities negative | collection created without cosine | `rm memory_store/`, recreate with `metadata={"hnsw:space": "cosine"}` |
| `attempt to write a readonly database` | store deleted while the client was open | exit; delete; start again |
| irrelevant memories retrieved | k too high, no floor, or the wrong query text | lower k; drop under 0.2; embed the *question*, not the whole context |
| context still explodes | trigger never fires, or you kept the old turns after summarising | print the buffer length every turn |
| remembers junk | `should_remember()` too loose | preferences and durable facts only; questions and answers are never stored |
| cites nothing | system prompt says *if relevant* | say *apply* and *cite each memory you applied* |
| stale memory misleads | no date, no type | store `timestamp` and `type`; then decay or delete by type |
| `â€"` in the terminal | Windows cp1252 | the `reconfigure` block at the top of the starter |

---

<div align="center" style="padding:14px; border-top:2px solid #0078d4; margin-top:34px;">
  <p style="margin:0 0 8px 0;">
    <img src="../assets/jhf-logo.png" alt="JHF" height="28" style="vertical-align:middle; margin:0 14px; background:#ffffff; padding:6px 10px; border-radius:6px;" />
    <img src="../assets/comcec-logo.png" alt="COMCEC" height="40" style="vertical-align:middle; margin:0 14px; background:#ffffff; padding:6px 10px; border-radius:6px;" />
  </p>
  <p style="color:#888; font-size:13px; margin:0;">
    <strong>JHF Agentic AI Bootcamp</strong> &mdash; Module 6 Lab<br/>
    Lead Trainer: <a href="https://www.linkedin.com/in/alaaldin-ahmed-260266150">Alaaldin Ahmed</a><br/>
    Organized by Jerusalem High-Tech Foundry (JHF) &middot; In partnership with COMCEC
  </p>
</div>
