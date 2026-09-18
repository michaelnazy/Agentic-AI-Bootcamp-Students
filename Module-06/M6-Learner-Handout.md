<!-- JHF-BRAND -->
<div align="center" style="padding:28px 20px; background:#ffffff; border:2px solid #e0e0e0; border-radius:12px;">
  <p style="margin:0 0 16px 0;">
    <img src="../assets/jhf-logo.png" alt="Jerusalem High-Tech Foundry (JHF)" height="54" style="vertical-align:middle; margin:0 22px;" />
    <img src="../assets/comcec-logo.png" alt="COMCEC - Cooperation for Development" height="72" style="vertical-align:middle; margin:0 22px;" />
  </p>
  <h1 style="color:#1a3c5e; margin:6px 0;">Agentic AI Bootcamp</h1>
  <h3 style="color:#0078d4; margin:4px 0; font-weight:600;">Module 6 &middot; Memory Systems &mdash; Learner Handout</h3>
  <hr style="border:0; border-top:1px solid #0078d4; width:60%; margin:16px auto;" />
  <p style="font-size:14px; color:#555; margin:6px 0;">
    <strong>Lead Trainer</strong><br/>
    <a href="https://www.linkedin.com/in/alaaldin-ahmed-260266150" target="_blank">Alaaldin Ahmed</a>
  </p>
  <p style="font-size:12.5px; color:#777; margin:8px 0 0 0;">
    Organized by <strong>Jerusalem High-Tech Foundry (JHF)</strong> &nbsp;&middot;&nbsp; In partnership with <strong>COMCEC</strong>
  </p>
</div>

# Module 6 — Memory Systems: Short-Term & Long-Term
## Learner Handout

> **Duration:** 4 hours · **Prereq:** M1–M5B.
> **You need:** the Module-02 venv (Python 3.12), `pip install -r requirements.txt` (chromadb brings its own local embeddings — no second key), your key in the repo-root `.env`, GitHub Copilot.
> **Start at `README.md`** in this folder — it has the setup check and the four-hour shape.
> Today your agent gains **memory** — within and across sessions — and you learn to **engineer its context**.

![Where we are in the stack — Memory](../assets/diagrams/augmented-llm-memory.png)

> *Book alignment: this module follows **Ch. 4 "Memory"** of the reference book (**An Illustrated Guide to AI Agents**, M. Grootendorst). Memory is framed there as the module that turns a forgetful LLM into an agent — and **context engineering** is its headline idea.*

---

## Learning Objectives

After this module you can:
1. **Implement short-term memory** (conversation buffer + summarization) to manage the context window.
2. **Implement long-term memory** (embed → vector store → retrieve) that persists across runs.
3. **Design memory policies**: what to write, when to summarize, what to forget.
4. **Distinguish memory types** (working, episodic, semantic, procedural) and map RAG-as-memory.
5. **Engineer the context**: select, compress, and order what the LLM sees — not just *what* to store, but *how to present it*.

---

## 1. Short-Term Memory & Context Management

In M1 you resent the whole history every step — that doesn't scale and isn't durable.

- **Conversation buffer:** recent turns kept in context (working memory).
- **Context window is finite:** keeping everything raises cost and hits limits.
- **Summarization:** compress older turns into a running summary; keep recent turns verbatim.
- **Triggers:** summarize every N turns, or when token count crosses a threshold.

> This fixes the "works but costs a fortune" problem from M1.

---

## 2. Long-Term Memory (Vector Store + Retrieval)

```
   WRITE:  interaction ─▶ embed ─▶ store vector (+metadata) in vector DB
   READ:   new query  ─▶ embed ─▶ similarity search ─▶ top-k memories ─▶ inject into context
```

- **Embeddings** turn text into vectors; similar meaning → nearby vectors.
- **Vector DB** stores memories; on a new query you **retrieve top-k** and inject them.
- This is **RAG used as memory**.
- **Persistence:** stored on disk/DB → memory survives restarts and sessions (the durable upgrade over M1).
- **Metadata** (source, timestamp, type) lets you **cite** and filter.

---

## 3. Memory Types & Policies

| Type | What | Example |
|---|---|---|
| **Working** | Current task context | active conversation buffer |
| **Episodic** | Specific past events | "last week you asked about X" |
| **Semantic** | Distilled facts/preferences | "you prefer metric units" |

**The three policies you must design:**
- **Write:** what's worth storing (preferences, durable facts — not every token).
- **Summarize:** when to compress; what to keep verbatim.
- **Evict/Forget:** TTL/staleness, relevance decay, explicit deletion (privacy).

---

## 4. Cost of Context & What NOT to Remember

- Every remembered token is **recurring cost** (retrieved/resent repeatedly). Memory isn't free.
- **Don't remember:** secrets/PII you shouldn't store, transient noise, anything cheap to recompute.
- **Staleness:** timestamp and decay old memories.
- **Privacy:** be deliberate; support forget/delete.

> Good memory design is as much about **forgetting** as remembering.

---

## 5. Context Engineering — Optimizing the Whole Context

> *Book alignment: the flagship idea of Ch. 4. Where **prompt engineering** tweaks the user/system message, **context engineering** optimizes the **entire** context window so the LLM produces the best output.*

Recall the M0 idea: **an LLM is a function; to improve the output, improve the input tokens.** Memory is the *source* of context; context engineering is *how you assemble it*.

### 5.1 What's actually in the context?
Four sources — each a memory type you already know:

| In the context | Memory type | Example |
|---|---|---|
| **System prompt** (rules, persona) | procedural | "You are a research assistant. Cite sources." |
| **Conversation history** | working | the last few turns |
| **Past experiences** (actions/observations) | episodic | "already searched arXiv; got 5 abstracts" |
| **Retrieved facts** (RAG) | semantic | top-k chunks from your vector store |

### 5.2 More context ≠ better
Filling a giant window backfires:
- **Lost-in-the-middle** — models attend best to the **start** and **end**; info in the middle gets missed (like human primacy/recency).
- **Context rot** — quality drops as you add irrelevant tokens; benchmarks like **RULER** show models that "pass" simple retrieval still degrade on real long-context reasoning.
- **Cost & latency** — every token is paid for and slows the response (the M11 theme).

### 5.3 The four levers (apply in the lab)
1. **Track & store** — decide up front what to log (agent actions, tool outputs, user feedback, `PLAN.md`).
2. **Select** — retrieve only what's relevant; **re-rank** results and keep the top few (not everything the vector search returned).
3. **Compress** — summarize; drop near-duplicates (**MMR**/dedup) so each kept item adds *new* information.
4. **Order** — put the most important context at the **start or end**, not buried in the middle.

### 5.4 Context as the specification
The context you feed an agent (the query, `PLAN.md`, `REQUIREMENTS.md`, the codebase) **is the spec of the work** — and a record of *why* the agent did what it did. Track it, don't throw it away: it's your best tool for **debugging, reproducibility, and teamwork**. (You'll keep a `PLAN.md` in the Capstone for exactly this reason.)

> **One-line takeaway:** context engineering is *"the right information, in the right amount, in the right place."*

---

## 6. Today's Lab (preview)

First, **four demos** (`demos/`) — each prints one number: a restart wipes the model's "memory" and a folder fixes it; resending history is a ramp and summarising is a sawtooth (33% saved at 12 turns); dumping 31 notes costs 26× a top-3 retrieval; and similarity ranks a 400-day-old fact above a 3-day-old one until *you* write the policy.

Then you build the **Personal Knowledge Assistant**:
- **Part 1 (45 min):** conversation buffer + summarisation to keep context bounded.
- **Part 2 (65 min):** long-term vector memory with metadata; persist to disk; prove recall **across a restart**; cite what you recalled.
- **Part 3 (30 min, `exercise/EXERCISE.md`):** context engineering, measured — **select** (top-k + threshold), **compress** (dedup by cosine), **order** (memories last) — and a prompt-size number for each.

Full steps: **`M6-Lab-Worksheet.md`**. Starter: **`starter-code/memory_agent_starter.py`**. Concepts on the board: **`M6-Whiteboard.html`**.

Run it as two commands in two processes:
```
python memory_agent.py --run1
python memory_agent.py --run2
```

**Definition of done:**
- **Run 1:** you tell it "I prefer metric units; I'm researching renewable energy" → stored as memories.
- **Restart the process.**
- **Run 2:** you ask "a quick figure for solar capacity" → it **retrieves** your preferences, answers in metric, and **cites** the memory used. Context stays bounded throughout.

---

## 7. Deliverables (graded — completes the Phase 3 mini-project)

1. **`memory_agent.py`** — the Personal Knowledge Assistant: short-term summarization + persistent long-term vector memory with citation.
2. **Cross-restart demo** — evidence (logs/screens) that a memory stored in Run 1 is recalled in Run 2.
3. **Memory-policy note (½ page)** — your write/summarize/evict choices **and one context-engineering lever** you applied (select/compress/order) with the measured prompt-size impact. Template: the end of `exercise/EXERCISE.md`.

---

## 8. Key Terms

| Term | Meaning |
|---|---|
| Working / episodic / semantic / procedural memory | Current context / past events / distilled facts / how-to & rules. |
| Conversation buffer | Recent turns held in context. |
| Summarization | Compressing old turns to bound context. |
| Embedding | Vector representation of text by meaning. |
| Vector store | DB of memory vectors for similarity retrieval. |
| Top-k retrieval | Fetching the k most relevant memories. |
| Write/summarize/evict policy | What to store / when to compress / what to forget. |
| **Context engineering** | Optimizing the whole context (select, compress, order) — not just the prompt. |
| **Lost-in-the-middle / context rot** | Quality loss from poorly-placed or excessive context. |
| **Context as specification** | Treating the agent's context (query, `PLAN.md`) as the tracked spec of the work. |

---

## 9. Quiz (5 min)

1. What problem does summarization solve in short-term memory?
2. Describe the write and read paths of long-term vector memory.
3. What makes long-term memory durable across runs?
4. Distinguish working, episodic, and semantic memory.
5. Name the three memory policies you must design.
6. Why is "remember everything" a bad default?
7. How do you let the assistant cite the memory it used?
8. This is RAG used as ___.

---

<div align="center" style="padding:14px; border-top:2px solid #0078d4; margin-top:34px;">
  <p style="margin:0 0 8px 0;">
    <img src="../assets/jhf-logo.png" alt="JHF" height="28" style="vertical-align:middle; margin:0 14px; background:#ffffff; padding:6px 10px; border-radius:6px;" />
    <img src="../assets/comcec-logo.png" alt="COMCEC" height="40" style="vertical-align:middle; margin:0 14px; background:#ffffff; padding:6px 10px; border-radius:6px;" />
  </p>
  <p style="color:#888; font-size:13px; margin:0;">
    <strong>JHF Agentic AI Bootcamp</strong> &mdash; Module 6<br/>
    Lead Trainer: <a href="https://www.linkedin.com/in/alaaldin-ahmed-260266150">Alaaldin Ahmed</a><br/>
    Organized by Jerusalem High-Tech Foundry (JHF) &middot; In partnership with COMCEC
  </p>
</div>

