<!-- JHF-BRAND -->
<div align="center" style="padding:28px 20px; background:#ffffff; border:2px solid #e0e0e0; border-radius:12px;">
  <p style="margin:0 0 16px 0;">
    <img src="../../assets/jhf-logo.png" alt="Jerusalem High-Tech Foundry (JHF)" height="54" style="vertical-align:middle; margin:0 22px;" />
    <img src="../../assets/comcec-logo.png" alt="COMCEC - Cooperation for Development" height="72" style="vertical-align:middle; margin:0 22px;" />
  </p>
  <h1 style="color:#1a3c5e; margin:6px 0;">Agentic AI Bootcamp</h1>
  <h3 style="color:#0078d4; margin:4px 0; font-weight:600;">Module 6 &middot; Part 3 Exercise &mdash; Context Engineering, Measured</h3>
  <hr style="border:0; border-top:1px solid #0078d4; width:60%; margin:16px auto;" />
  <p style="font-size:14px; color:#555; margin:6px 0;">
    <strong>Lead Trainer</strong><br/>
    <a href="https://www.linkedin.com/in/alaaldin-ahmed-260266150" target="_blank">Alaaldin Ahmed</a>
  </p>
  <p style="font-size:12.5px; color:#777; margin:8px 0 0 0;">
    Organized by <strong>Jerusalem High-Tech Foundry (JHF)</strong> &nbsp;&middot;&nbsp; In partnership with <strong>COMCEC</strong>
  </p>
</div>

# Module 6 — Part 3 Exercise
## Context engineering, measured

> **Time:** 30 minutes · **After** the lab, not instead of it.
> **Files:** `starter-code/context_lab_starter.py` → save as `context_lab.py`
> **Goal:** the same 20 memories and the same question, built into a context four different
> ways — and a **number** for each. You leave with the half-page policy note that handout §7
> asks for, already written.

The lab gave your agent a memory. This exercise is about what you *show* the model
from that memory. Handout §5.3 named four levers: **track, select, compress, order**.
You will pull three of them and measure each pull.

> **The one thing to leave with:** memory is what you store. Context is what you show
> the model. They are different decisions, and the second one has a price on it.

---

## Step 0 — a store to measure (2 min)

```powershell
cd Module-06\exercise
..\..\Module-02\.venv\Scripts\python.exe seed_memories.py
```

Twenty memories: 4 preferences, 8 facts, 8 episodic. Three of the preferences say
"metric" in different words and two facts are repeated. That is deliberate.

**Or use your own.** If your `memory_agent.py` from the lab works, open the starter and
change `DB_DIR` to point at your `memory_store/`. Same measurements, your memories.
(Then Step 3 will only drop something if you actually stored a duplicate.)

🧪 **Checkpoint.** Run the starter as-is. It prints one row — the baseline — and then
`-- not yet: Step 2`. That is the correct starting state.

---

## Step 1 — baseline (3 min)

Already implemented. The starter retrieves the **top 10** memories and puts them in the
**middle** of the context: rules → memories → the earlier conversation → the question.

Write down the baseline row. You need it for every percentage below.

🧪 **Checkpoint.** Read the ten memories it retrieved. How many actually help answer
*"Give me a quick figure for solar capacity"*? Two, maybe three. You just paid for ten.

---

## Step 2 — select (7 min) · `select()`

The list is already ranked by similarity. Keep at most `k`, and only those above
`min_sim`. Print what you dropped.

🧪 **Checkpoint.** Three memories left; the row shows a saving. Now ask yourself what
the threshold *protected you from*: look at the similarity of the first thing you dropped.

---

## Step 3 — compress (8 min) · `compress()`

Walk the kept list in order. A memory earns its place only if its cosine similarity to
**every** memory already kept is below `threshold`. The embeddings are already on each
row (`m["embedding"]`) and `cosine()` is written for you.

🧪 **Checkpoint.** At `0.70` it drops the second IRENA line. Print the pair and the
cosine. Then try `0.60` and see what happens to the three "metric" lines. Then `0.55`.
**Where does it start deleting things that were not duplicates?** That number is the
whole lesson of this step.

---

## Step 4 — order (5 min) · `build_context(position="last")`

Same four ingredients, memories moved from the middle to **immediately before the
question**. Prompt size does not change. Does the answer?

🧪 **Checkpoint.** Compare the `cited a memory` column and the answers side by side.
On our runs, moving the memories last sometimes changed the answer and sometimes did not —
one run only cited properly with memories last; the next cited in both. **Write down what
you saw**, either way. Then say why this lever is different from the other two: it costs
nothing, so the only reason not to pull it is if it makes things worse.

---

## The table

Copy the receipt the script prints at the end:

```
  variant                                 memories   prompt size   cited   saved
  1 baseline  top-10, middle ..........      10        ~____         __      —
  2 select    top-3 above threshold ....       3        ~____         __     __%
  3 compress  minus near-duplicates ....       _        ~____         __     __%
  4 order     same content, last ......       _        ~____         __     __%
```

Then one line: **which lever bought the most, and what did it cost you?** (Hint: one
of the four costs nothing at all.)

---

## Done when

- [ ] Baseline row written down, from *your* run.
- [ ] `select()` works and the row shows a saving.
- [ ] `compress()` drops at least one memory and prints the pair and the cosine.
- [ ] The `order` row is filled in, with the two answers compared.
- [ ] The policy note below is written.

---

## Self-grade before you submit

| # | Criterion | You pass when |
|:-:|---|---|
| 1 | Measured, not described | Every row has a real number from your run, not the one in this document |
| 2 | One lever, one number | The note names a lever and the saving it produced, as a percentage |
| 3 | Dedup is real | At least one drop, with the cosine printed |
| 4 | Order was tested | Both answers pasted, and a sentence on the difference (or on there being none) |
| 5 | Forgetting is designed | The note says what you would *not* store, and when you would delete |

4 of 5 = PASS.

---

## 🔥 The memory-policy note (this is handout deliverable 3)

Half a page. Four headings, two or three sentences under each:

```
WRITE      what your should_remember() keeps, and one thing it deliberately refuses
SUMMARISE  your trigger (turns or tokens), what stays verbatim, what the summary drops
EVICT      what goes stale, how you would detect it (TTL / decay / type), and the privacy case
THE LEVER  select | compress | order — which, what it saved (%), and what it risked
```

Submit it with `memory_agent.py` and the cross-restart evidence from the lab.

---

## Stretch (optional)

- **Track.** The fourth lever. Log every context you send (`messages` → a JSONL file with
  a timestamp). Now you can answer *"why did it say that?"* after the fact. That log *is*
  handout §5.4's "context as specification".
- **Re-rank with a second signal.** Score = similarity × recency, like demo 4. Does the
  top-3 change?
- **Metadata filter before similarity.** Ask chromadb for `type=preference` only. Cheaper
  than embedding-then-filtering, and it never returns an episode by mistake.

---

## Troubleshooting

| symptom | cause | fix |
|---|---|---|
| `empty store — run seed_memories.py first` | you ran the starter from a different folder, or Step 0 was skipped | `cd Module-06\exercise` then seed; or fix `DB_DIR` |
| `compress` drops nothing | threshold too high for this embedding model | print the cosines; true duplicates sit around 0.72–0.79 |
| `compress` drops everything | threshold too low | anything under ~0.55 is deleting real information |
| `cited: no` on every row | the model is paraphrasing the citation format | look at the answer text; the rule accepts *from your / my / the stored* |
| `ModuleNotFoundError: chromadb` | wrong interpreter | `Module-02\.venv\Scripts\python.exe`, not `python` |
| numbers differ from the ones in this document | they should | the *shape* is what matters: 10 → 3 → 2, and order is free |

---

<div align="center" style="padding:14px; border-top:2px solid #0078d4; margin-top:34px;">
  <p style="margin:0 0 8px 0;">
    <img src="../../assets/jhf-logo.png" alt="JHF" height="28" style="vertical-align:middle; margin:0 14px; background:#ffffff; padding:6px 10px; border-radius:6px;" />
    <img src="../../assets/comcec-logo.png" alt="COMCEC" height="40" style="vertical-align:middle; margin:0 14px; background:#ffffff; padding:6px 10px; border-radius:6px;" />
  </p>
  <p style="color:#888; font-size:13px; margin:0;">
    <strong>JHF Agentic AI Bootcamp</strong> &mdash; Module 6 Exercise<br/>
    Lead Trainer: <a href="https://www.linkedin.com/in/alaaldin-ahmed-260266150">Alaaldin Ahmed</a><br/>
    Organized by Jerusalem High-Tech Foundry (JHF) &middot; In partnership with COMCEC
  </p>
</div>
