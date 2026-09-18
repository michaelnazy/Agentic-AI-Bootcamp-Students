"""
Module 6 — Part 3 exercise — STARTER
Context engineering, measured. Same memories, same question, four ways of
building the context. You write three functions and fill in one table.

    python seed_memories.py                       # once, from exercise/
    python starter-code/context_lab_starter.py    # runs what you have so far

STEP 0  (optional) point DB_DIR at YOUR memory_store from the lab instead of the seed.
STEP 1  baseline   — already works. Run it. Write the number down.
STEP 2  select()   — keep the top-k by similarity, above a threshold
STEP 3  compress() — drop near-duplicates (cosine between memory embeddings)
STEP 4  build_context(position="last") — same content, memories moved to the END

The receipt printed for every variant is the deliverable. Copy the numbers into
EXERCISE.md's table.
"""

from __future__ import annotations

import math
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = Path(__file__).resolve().parent            # exercise/starter-code/
load_dotenv(HERE.parent.parent.parent / ".env")   # repo-root .env

# STEP 0: to use your own lab memories, change this to  ...parent.parent / "memory_store"
DB_DIR = HERE.parent / "exercise_store"

QUERY = "Give me a quick figure for solar capacity."
SYSTEM = ("You are a personal research assistant. Be concise (max 80 words). Follow any preference in the "
          "RECALLED MEMORIES. When you rely on a memory, cite it exactly as (from your stored <type>, <date>).")

# a canned earlier conversation, so that "middle" and "last" mean something
PRIOR_TURNS = [
    ("user", "I'm putting together the renewable energy section of the brief this week."),
    ("assistant", "Understood. Tell me which figures you need and I will keep them short."),
    ("user", "Start with the headline numbers, then we can go into regional detail."),
    ("assistant", "Headline numbers first. Ready when you are."),
]

# ---------------------------------------------------------------- given ----
import chromadb  # noqa: E402
from langchain_openai import ChatOpenAI  # noqa: E402
import tiktoken  # noqa: E402

_client = chromadb.PersistentClient(path=str(DB_DIR))
collection = _client.get_or_create_collection("memories", metadata={"hnsw:space": "cosine"})
llm = ChatOpenAI(model=os.getenv("MODEL", "openai/gpt-4o-mini"), temperature=0,
                 base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
                 api_key=os.environ.get("OPENROUTER_API_KEY"))
_enc = tiktoken.get_encoding("o200k_base")


def count_tokens(messages) -> int:
    return sum(len(_enc.encode(text)) + 4 for _, text in messages)


def retrieve(query: str, k: int = 10) -> list[dict]:
    """Top-k memories with metadata, similarity AND the stored embedding (for Step 3)."""
    hits = collection.query(query_texts=[query], n_results=min(k, collection.count()),
                            include=["documents", "metadatas", "distances", "embeddings"])
    rows = []
    for doc, meta, dist, emb in zip(hits["documents"][0], hits["metadatas"][0],
                                    hits["distances"][0], hits["embeddings"][0]):
        rows.append({"text": doc, "type": meta["type"], "timestamp": meta["timestamp"],
                     "similarity": round(1 - dist, 3), "embedding": list(emb)})
    return sorted(rows, key=lambda r: -r["similarity"])


def memories_block(memories: list[dict]) -> str:
    return "RECALLED MEMORIES:\n" + "\n".join(
        f"{i}. [{m['type']}, {m['timestamp']}, sim {m['similarity']}] {m['text']}" for i, m in enumerate(memories, 1))


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    return dot / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)) or 1.0)


def measure(label: str, messages: list[tuple[str, str]], memories: list[dict]) -> dict:
    est = count_tokens(messages)
    resp = llm.invoke(messages)
    billed = (resp.usage_metadata or {}).get("input_tokens", 0)
    text = resp.content.strip()
    cited = re.search(r"\(from (your|my|the) stored", text, re.I) is not None
    row = {"label": label, "memories": len(memories), "estimate": est, "billed": billed, "cited": cited}
    print(f"\n== {label}")
    print(f"   memories in context: {len(memories):<3} prompt size (estimate / billed): {est} / {billed}"
          f"   cited a memory: {'YES' if cited else 'no'}")
    print("   " + text.replace("\n", "\n   "))
    return row


# ---------------------------------------------------------------- yours ----
def build_context(memories: list[dict], position: str = "middle") -> list[tuple[str, str]]:
    """position='middle': rules -> MEMORIES -> prior turns -> question   (given)
       position='last'  : rules -> prior turns -> MEMORIES -> question   (STEP 4)"""
    if position == "middle":
        return [("system", SYSTEM), ("system", memories_block(memories))] + PRIOR_TURNS + [("user", QUERY)]
    # TODO (Step 4): return the same four ingredients with the memories block placed
    # AFTER the prior turns, immediately before the question.
    raise NotImplementedError("Step 4: build_context(position='last')")


def select(memories: list[dict], k: int = 3, min_sim: float = 0.35) -> list[dict]:
    # TODO (Step 2): memories are already sorted by similarity. Keep at most k, and only
    # those with similarity >= min_sim. Print how many you dropped.
    raise NotImplementedError("Step 2: select()")


def compress(memories: list[dict], threshold: float = 0.70) -> list[dict]:
    # TODO (Step 3): walk the list in order; keep a memory only if its cosine() to EVERY
    # already-kept embedding is below `threshold`. Print each one you drop and what it duplicated.
    # (0.70 is a measured choice for this model: true duplicates sit at 0.72-0.79, the closest
    #  non-duplicate at 0.56. Try 0.60 afterwards and watch what happens to the three "metric" lines.)
    raise NotImplementedError("Step 3: compress()")


# ---------------------------------------------------------------- run ----
def main() -> None:
    print(f"[store: {DB_DIR}  memories: {collection.count()}]")
    if collection.count() == 0:
        sys.exit("empty store — run seed_memories.py first (or fix DB_DIR)")
    rows = []
    top10 = retrieve(QUERY, k=10)

    rows.append(measure("1 baseline  top-10, memories in the MIDDLE", build_context(top10, "middle"), top10))

    try:
        kept = select(top10)
        rows.append(measure("2 select    top-3 above threshold", build_context(kept, "middle"), kept))
        try:
            deduped = compress(kept)
            rows.append(measure("3 compress  top-3 minus near-duplicates", build_context(deduped, "middle"), deduped))
            try:
                rows.append(measure("4 order     same content, memories LAST", build_context(deduped, "last"), deduped))
            except NotImplementedError as e:
                print(f"\n-- not yet: {e}")
        except NotImplementedError as e:
            print(f"\n-- not yet: {e}")
    except NotImplementedError as e:
        print(f"\n-- not yet: {e}")

    print("\n" + "=" * 70)
    print(f"   {'variant':<44} {'mem':>3}  {'est':>5}  {'billed':>6}  cited  saved")
    base = rows[0]["billed"] or rows[0]["estimate"]
    for r in rows:
        used = r["billed"] or r["estimate"]
        saved = f"{(1 - used / base) * 100:>4.0f}%" if r is not rows[0] else "   —"
        print(f"   {r['label']:<44} {r['memories']:>3}  {r['estimate']:>5}  {r['billed']:>6}  "
              f"{'YES ' if r['cited'] else 'no  '}  {saved}")
    print("=" * 70)
    print("   Copy these into the table in EXERCISE.md. The half-page policy note explains ONE of them.")


if __name__ == "__main__":
    main()
