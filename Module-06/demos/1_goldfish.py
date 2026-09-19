"""
1 · the goldfish — same model, same prompts, different folder.

Two agents get the same two prompts. One keeps nothing between processes.
The other writes to a folder on disk and reads from it on the way back in.

    python 1_goldfish.py --reset --run1      # "Call me Ahmad. I prefer metric units, and I always want answers as exactly three short bullet points. I'm researching renewable energy."
    python 1_goldfish.py --run2              # NEW PROCESS: "How long is a marathon, and how fast do the elite runners go?"

The restart between the two commands is the demo. Do not skip it.
Line to land: "Same model. Same prompts. The only thing that changed is a folder on disk."
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import os
import re
import time

from _common import STORE_ROOT, chat, open_collection, reset_store, rule, similarity, SYSTEM

NAME = "goldfish"
RUN1 = ("Call me Mohammad. I prefer metric units, and I always want answers as exactly three short "
        "bullet points. I'm researching renewable energy.")
RUN2 = "How long is a marathon, and how fast do the elite runners go?"

# ---- a 30-line memory system: the write policy, the write path, the read path
_PREF = re.compile(r"\b(i prefer|i like|i always|i never|call me|my name is)\b", re.I)
_FACT = re.compile(r"\b(i'm researching|i am researching|i'm working on|my project|my role|i work)\b", re.I)


def clauses(text: str) -> list[str]:
    parts = re.split(r";|\.\s+|\band\b(?=\s+i\b|\s+i'm\b|\s+i am\b)", text, flags=re.I)
    return [p.strip(" .,") for p in parts if p.strip(" .,")]


def classify(clause: str) -> str | None:
    if _PREF.search(clause):
        return "preference"
    if _FACT.search(clause):
        return "fact"
    return None


def goldfish(user_text: str) -> tuple[str, int]:
    """No memory at all: system prompt + this one message."""
    return chat([("system", SYSTEM), ("user", user_text)])


def memory_agent(user_text: str, col) -> tuple[str, int, list, list]:
    stored = []
    for c in clauses(user_text):                                   # WRITE policy + path
        kind = classify(c)
        if kind:
            col.upsert(ids=[hashlib.sha256(c.lower().encode()).hexdigest()[:16]],   # dedup id, not security
                       documents=[c],
                       metadatas=[{"type": kind, "timestamp": dt.date.today().isoformat(), "ts": time.time()}])
            stored.append((kind, c))

    recalled = []                                                  # READ path, two rules:
    if col.count():
        prefs = col.get(where={"type": "preference"}, include=["documents", "metadatas"])
        for doc, meta in zip(prefs["documents"], prefs["metadatas"]):   # 1. preferences: ALWAYS loaded
            recalled.append((doc, "preference", meta["timestamp"], None))
        hits = col.query(query_texts=[user_text], n_results=min(3, col.count()),
                         where={"type": {"$ne": "preference"}},
                         include=["documents", "metadatas", "distances"])
        for doc, meta, dist in zip(hits["documents"][0], hits["metadatas"][0], hits["distances"][0]):
            if similarity(dist) >= 0.2:                               # 2. facts: only if RELEVANT
                recalled.append((doc, meta["type"], meta["timestamp"], similarity(dist)))

    messages = [("system", SYSTEM + " If RECALLED MEMORIES are given, apply every preference in them "
                 "(how to address the user, answer format, units). End the answer with one citation per "
                 "memory you used, written literally like this example: (from your stored preference, 2026-01-31).")]
    if recalled:
        block = "\n".join(f"{i}. [{kind}, {ts}] {doc}" for i, (doc, kind, ts, _) in enumerate(recalled, 1))
        messages.append(("system", "RECALLED MEMORIES:\n" + block))
    messages.append(("user", user_text))
    text, ptoks = chat(messages)
    return text, ptoks, stored, recalled


def show(label: str, text: str, ptoks: int) -> None:
    print(f"\n{label}   (prompt size: {ptoks})")
    for line in text.splitlines():
        print(f"   {line}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run1", action="store_true")
    ap.add_argument("--run2", action="store_true")
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()
    if args.reset:
        reset_store(NAME)
        print(f"[store wiped: {STORE_ROOT / NAME}]")
    if not (args.run1 or args.run2):
        ap.print_help()
        return

    col = open_collection(NAME)
    prompt = RUN1 if args.run1 else RUN2
    rule(f"RUN {'1' if args.run1 else '2'} · pid {os.getpid()} · memories on disk at start: {col.count()}")
    print(f'\n> "{prompt}"')

    g_text, g_toks = goldfish(prompt)
    m_text, m_toks, stored, recalled = memory_agent(prompt, col)

    show("GOLDFISH  (no memory)", g_text, g_toks)
    show("MEMORY AGENT", m_text, m_toks)

    rule("receipt")
    print(f"   goldfish      stored: 0   recalled: 0")
    print(f"   memory agent  stored: {len(stored)}   recalled: {len(recalled)}"
          + (f"   sims: {', '.join(str(r[3]) for r in recalled if r[3] is not None)}"
             if any(r[3] is not None for r in recalled) else ""))
    for kind, c in stored:
        print(f"      + wrote {kind}: \"{c}\"")
    for doc, kind, ts, sim in recalled:
        how = "always loaded" if sim is None else f"similarity {sim}"
        print(f"      < read  {kind} ({ts}, {how}): \"{doc}\"")
    if args.run2:
        cited = re.search(r"\(from your stored \w+, \d{4}-\d{2}-\d{2}\)", m_text) is not None
        print(f"   citation in the memory agent's answer: {'YES' if cited else 'no'}")
    print(f"   store: {STORE_ROOT / NAME}")
    if args.run1:
        print("\nNow STOP this process and run:   python 1_goldfish.py --run2")


if __name__ == "__main__":
    main()
