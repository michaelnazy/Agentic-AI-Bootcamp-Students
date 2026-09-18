"""
4 · the forgetting policy — similarity tells you what is related, not what is still true.

Eight memories with REAL backdated timestamps. Three of them are about London
and 350-400 days old. "I moved to Amman last week" is 3 days old. Ask "Where am
I based?" under three policies:

  1. raw          top-3 by cosine similarity            (three London memories fill the
                                                         top-3; Amman is never shown)
  2. decayed      score = sim * 0.5 ** (age / HALF_LIFE) for EPISODIC memories only
                  (preferences do not decay)             (Amman wins)
  3. evicted      collection.delete(episodic AND older than 180 days)   (all London is gone)

    python 4_forgetting.py            # no API needed
    python 4_forgetting.py --ask      # + one LLM answer per policy, to show the answer flip

Line to land: "Similarity tells you what is related. It cannot tell you what is
still true. That is a policy you write, not a property of the database."
"""

from __future__ import annotations

import argparse
import datetime as dt
import time

from _common import chat, open_collection, reset_store, rule, similarity

NAME = "forgetting"
QUESTION = "Where am I based these days?"
HALF_LIFE_DAYS = 30
EVICT_AFTER_DAYS = 180

#            text                                                     type          age (days)
MEMORIES = [
    ("I'm based in London.",                                          "episodic",   400),
    ("I'm London-based.",                                             "episodic",   380),
    ("I work out of London.",                                         "episodic",   350),
    ("I moved to Amman last week.",                                   "episodic",     3),
    ("I prefer metric units.",                                        "preference", 200),
    ("My project is a solar-capacity dashboard for a policy brief.",  "fact",       120),
    ("Last month I attended a wind-energy conference in Copenhagen.", "episodic",    35),
    ("I usually work from a cafe near the office on Thursdays.",      "episodic",    90),
]


def seed(col) -> None:
    now = time.time()
    col.add(
        ids=[f"m{i}" for i in range(len(MEMORIES))],
        documents=[t for t, _, _ in MEMORIES],
        metadatas=[{"type": kind, "ts": now - days * 86400,
                    "timestamp": (dt.date.today() - dt.timedelta(days=days)).isoformat()}
                   for _, kind, days in MEMORIES],
    )


def top(col, k: int = 3) -> list[dict]:
    hits = col.query(query_texts=[QUESTION], n_results=min(k, col.count()),
                     include=["documents", "metadatas", "distances"])
    out = []
    for doc, meta, dist in zip(hits["documents"][0], hits["metadatas"][0], hits["distances"][0]):
        age = (time.time() - meta["ts"]) / 86400
        out.append({"text": doc, "type": meta["type"], "age": age, "date": meta["timestamp"],
                    "sim": similarity(dist)})
    return out


def decayed(rows: list[dict]) -> list[dict]:
    for r in rows:
        factor = 0.5 ** (r["age"] / HALF_LIFE_DAYS) if r["type"] == "episodic" else 1.0
        r["score"] = round(r["sim"] * factor, 3)
    return sorted(rows, key=lambda r: -r["score"])


def table(title: str, rows: list[dict], key: str) -> None:
    rule(title)
    print(f"\n   {key:<6} sim     age(d)  type        memory")
    for r in rows:
        print(f"   {r.get(key, r['sim']):<6} {r['sim']:<7} {r['age']:>5.0f}  {r['type']:<11} {r['text']}")
    print(f"\n   -> winner: \"{rows[0]['text']}\"")


def maybe_ask(rows: list[dict], enabled: bool) -> None:
    if not enabled:
        return
    block = "\n".join(f"- [{r['type']}, {r['date']}] {r['text']}" for r in rows)
    text, _ = chat([("system", "Answer from the memories in one short sentence. Cite the date you relied on.\n"
                               "MEMORIES:\n" + block), ("user", QUESTION)])
    print(f"   LLM: {text}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ask", action="store_true", help="also ask the LLM under each policy")
    args = ap.parse_args()

    reset_store(NAME)
    col = open_collection(NAME)
    seed(col)
    print(f'{col.count()} memories on disk. Question: "{QUESTION}"\n')

    raw = top(col)
    table("1 · raw — top-3 by similarity", raw, "sim")
    maybe_ask(raw, args.ask)

    dec = decayed(top(col, k=col.count()))[:3]
    table(f"2 · decayed — sim x 0.5^(age/{HALF_LIFE_DAYS}d), episodic only", dec, "score")
    maybe_ask(dec, args.ask)

    cutoff = time.time() - EVICT_AFTER_DAYS * 86400
    stale = col.get(where={"$and": [{"type": "episodic"}, {"ts": {"$lt": cutoff}}]})
    col.delete(ids=stale["ids"])
    ev = top(col)
    table(f"3 · evicted — deleted {len(stale['ids'])} episodic memor{'y' if len(stale['ids']) == 1 else 'ies'} "
          f"older than {EVICT_AFTER_DAYS}d; {col.count()} left", ev, "sim")
    for doc in stale["documents"]:
        print(f"   x deleted: \"{doc}\"")
    maybe_ask(ev, args.ask)

    rule("receipt")
    print("   Raw ranking filled the top-3 with London. Amman was rank 4: the model never saw it.")
    print("   The database was not wrong. It answered what is SIMILAR. 'What is still TRUE' is your policy.")
    print("   Note the preference survived every policy: preferences do not decay; episodes do.")


if __name__ == "__main__":
    main()
