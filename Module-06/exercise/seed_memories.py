"""
seed_memories.py — 20 memories for the context-engineering exercise.

    python seed_memories.py           # (re)creates exercise/exercise_store/

Deliberately included:
  - THREE near-duplicates of the metric preference   (Step 3, compress/dedup, will catch them)
  - two pairs of facts that say the same thing twice  (same)
  - eight episodic notes that are related to solar but say nothing useful about the query
    (Step 2, select, should leave most of them out)

If your own memory_agent.py works, you can skip this and point the exercise at
YOUR store instead — see EXERCISE.md, Step 0.
"""

from __future__ import annotations

import datetime as dt
import shutil
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import chromadb  # noqa: E402

HERE = Path(__file__).resolve().parent
STORE = HERE / "exercise_store"

#            text                                                                       type          age (days)
MEMORIES = [
    # preferences (4) — three of them are the SAME preference in different words
    ("I prefer metric units.",                                                         "preference",  40),
    ("Please use metric: km, kg, degrees C.",                                          "preference",  12),
    ("Use SI units in any figures you show me.",                                       "preference",   5),
    ("Keep answers under 80 words unless I ask for detail.",                           "preference",  30),
    # facts (8) — two pairs repeat themselves
    ("My solar numbers come from IRENA's 2024 capacity statistics.",                   "fact",        20),
    ("The solar dataset I use is the IRENA capacity statistics, 2024 edition.",        "fact",         9),
    ("The policy brief is due on 3 October.",                                          "fact",        15),
    ("Deadline for the brief: 3 October.",                                             "fact",         4),
    ("I'm researching renewable energy for a national policy brief.",                  "fact",        45),
    ("My audience is policy staff, not engineers.",                                    "fact",        25),
    ("I work on the energy team at a think tank in Amman.",                            "fact",        60),
    ("Our house style writes gigawatts as GW, not Gigawatts.",                         "fact",        18),
    # episodic (8) — related to solar, useless for the query
    ("Yesterday I compared three solar datasets and found they disagree by 8 percent.", "episodic",    1),
    ("Last week I sent the draft outline to Rana for comments.",                       "episodic",     7),
    ("I attended a webinar on offshore wind auctions in March.",                       "episodic",   190),
    ("The March spreadsheet had a units mismatch that took a day to find.",            "episodic",   180),
    ("I asked about grid storage options on Monday and got a long answer.",            "episodic",     3),
    ("I visited a rooftop solar installer's site in Zarqa last spring.",               "episodic",   150),
    ("Two weeks ago I flagged the capacity-factor chart as unclear.",                  "episodic",    14),
    ("I skipped the Thursday review because of a clash.",                              "episodic",     6),
]


def main() -> None:
    shutil.rmtree(STORE, ignore_errors=True)
    client = chromadb.PersistentClient(path=str(STORE))
    col = client.get_or_create_collection("memories", metadata={"hnsw:space": "cosine"})
    now = time.time()
    col.add(
        ids=[f"m{i:02d}" for i in range(len(MEMORIES))],
        documents=[t for t, _, _ in MEMORIES],
        metadatas=[{"type": kind, "source": "seed", "ts": now - days * 86400,
                    "timestamp": (dt.date.today() - dt.timedelta(days=days)).isoformat()}
                   for _, kind, days in MEMORIES],
    )
    kinds = {k: sum(1 for _, t, _ in MEMORIES if t == k) for k in ("preference", "fact", "episodic")}
    print(f"seeded {col.count()} memories -> {STORE}")
    print(f"   {kinds['preference']} preferences · {kinds['fact']} facts · {kinds['episodic']} episodic")
    print("   (3 say 'metric' in different words; 2 facts are repeated. That is on purpose.)")


if __name__ == "__main__":
    main()
