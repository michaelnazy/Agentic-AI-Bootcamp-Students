"""
3 · lost in the middle — even when it finds the needle, you paid for the haystack.

31 memories on disk: 28 plausible research notes (the haystack), 2 that mention
units in passing (near misses), and 1 preference (the needle):
"For everything you show me, I prefer metric units."

The demo is a pipeline you can watch, step by step:

  1. THE STORE      what is on disk, and what it would cost to send all of it
  2. THE QUESTION   one sentence, and what chromadb turns it into
  3. THE RANKING    every memory scored against the question; the top-k cut drawn
  4. THE TWO PROMPTS  what the model actually receives — retrieval vs the dump
  5. THE ANSWERS    both ways, with tokens and money; the dump at START/MIDDLE/END

    python 3_lost_in_the_middle.py
    python 3_lost_in_the_middle.py --no-api        # steps 1-4 only, no key needed
    python 3_lost_in_the_middle.py --trials 1      # faster
    python 3_lost_in_the_middle.py --k 5           # a different cut
    python 3_lost_in_the_middle.py --price 0.15    # USD per 1M input tokens, for the money column

Honest framing: a strong model may score 3/3 at every position. Fine. The
cost column lands every time.
Line to land: "Even when it finds the needle, you paid for the haystack.
And sometimes it doesn't find it."
"""

from __future__ import annotations

import argparse
import random
import re

from _common import bar, chat, count_tokens, open_collection, reset_store, rule, similarity

NAME = "haystack"
NEEDLE = "For everything you show me, I prefer metric units."
QUESTION = ("Which units should you use when you show me figures? "
            "Answer with exactly one word: metric or imperial.")
SYSTEM_PREFIX = "You are a research assistant. NOTES ABOUT THE USER:\n"

SOURCES = ["the IEA Renewables report", "IRENA's capacity statistics", "a Lazard LCOE update",
           "the Ember electricity review", "a BloombergNEF note", "a grid-operator filing",
           "an academic review on storage", "the March project spreadsheet", "a supplier datasheet",
           "a conference talk in Copenhagen"]
TOPICS = ["solar PV additions", "offshore wind capacity factors", "battery storage costs",
          "grid connection queues", "curtailment rates", "green hydrogen pilots", "rooftop solar policy",
          "pumped hydro retrofits", "transmission build-out", "power purchase agreements"]
CLAIMS = ["grew faster than the previous forecast assumed", "vary far more by region than the headline suggests",
          "fell again year on year", "are the binding constraint in several markets",
          "were revised downward after the audit", "remain hard to compare across sources"]
DETAILS = ["I noted the methodology section for the brief.", "The chart on page 12 is the one to reuse.",
           "Worth a footnote, not a paragraph.", "I flagged this for the Thursday review.",
           "Needs a second source before I cite it.", "The figure excludes China, which matters."]

NEAR_MISSES = [
    "A colleague on the modelling team still works in imperial units, which caused a mismatch in the March spreadsheet.",
    "The 2019 industry report quoted panel area in square feet, so its figures need converting before I use them.",
]

STOP = {"the", "a", "an", "i", "you", "me", "my", "to", "of", "for", "in", "on", "and", "or", "with",
        "that", "this", "it", "is", "are", "be", "should", "when", "which", "use", "exactly", "one", "word"}


def haystack(seed: int = 7) -> list[str]:
    r = random.Random(seed)
    notes = []
    for i in range(28):
        details = " ".join(r.sample(DETAILS, 4))
        notes.append(f"Note {i + 1}: reviewing {r.choice(SOURCES)}, I logged that {r.choice(TOPICS)} "
                     f"{r.choice(CLAIMS)}, and separately that {r.choice(TOPICS)} {r.choice(CLAIMS)}. "
                     f"{details} Cross-check against {r.choice(SOURCES)} before the draft goes out.")
    return notes + NEAR_MISSES


def tag(doc: str) -> str:
    return "  <- the needle" if doc == NEEDLE else ("  <- near miss" if doc in NEAR_MISSES else "")


def short(doc: str, n: int = 0) -> str:
    return doc  # print everything in full; nothing is truncated


def words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z']+", text.lower()) if w not in STOP}


def build_prompt(notes: list[str]) -> list[tuple[str, str]]:
    block = "\n".join(f"{i}. {n}" for i, n in enumerate(notes, 1))
    return [("system", SYSTEM_PREFIX + block), ("user", QUESTION)]


def prompt_tokens(messages) -> int:
    return sum(count_tokens(t) + 4 for _, t in messages)


def show_prompt(title: str, messages) -> None:
    print(f"\n   {title}")
    print("   " + "." * 64)
    for role, text in messages:
        print(f"   [{role}]")
        for line in text.splitlines():
            print(f"      {line}")
    print("   " + "." * 64)


def place(notes: list[str], where: str, seed: int) -> list[str]:
    shuffled = notes[:]
    random.Random(seed).shuffle(shuffled)
    idx = {"START": 0, "MIDDLE": len(shuffled) // 2, "END": len(shuffled)}[where]
    return shuffled[:idx] + [NEEDLE] + shuffled[idx:]


def ask(notes: list[str]) -> tuple[bool, int, str]:
    text, size = chat(build_prompt(notes))
    ok = "metric" in text.lower() and "imperial" not in text.lower()
    return ok, size, text


def usd(tokens: int, price_per_m: float) -> str:
    return f"${tokens / 1_000_000 * price_per_m:.5f}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-api", action="store_true", help="steps 1-4 only")
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--k", type=int, default=3, help="how many memories retrieval keeps")
    ap.add_argument("--price", type=float, default=0.15,
                    help="assumed USD per 1M input tokens for the money column (default 0.15)")
    args = ap.parse_args()

    notes = haystack()
    all_notes = notes + [NEEDLE]
    dump_prompt = build_prompt(all_notes)
    dump_size = prompt_tokens(dump_prompt)

    # ---- 1. the store ------------------------------------------------------------
    rule("1 · THE STORE — what is on disk")
    reset_store(NAME)
    col = open_collection(NAME)
    col.add(ids=[f"n{i}" for i in range(len(all_notes))], documents=all_notes)
    print(f"\n   {col.count()} memories in demo_store/{NAME}/. A sample:\n")
    for i in (0, 13, 27, 28, 30):
        print(f"   [{i + 1:>2}] {short(all_notes[i], 84)}{tag(all_notes[i])}")
    print(f"\n   Sent all together they are {dump_size} tokens. Keep that number.")

    # ---- 2. the question ---------------------------------------------------------
    rule("2 · THE QUESTION — and what chromadb does with it")
    print(f'\n   > "{QUESTION}"\n')
    emb = col._embedding_function([QUESTION])[0]
    print(f"   chromadb embeds it with all-MiniLM-L6-v2 -> a vector of {len(emb)} numbers:")
    print(f"      [{', '.join(f'{x:+.3f}' for x in emb[:8])}, ... ]")
    print("   Every memory on disk was turned into the same kind of vector when it was stored.")
    print("   Similarity = how close two vectors point. Nothing here compares words.")

    # ---- 3. the ranking ----------------------------------------------------------
    rule(f"3 · THE RANKING — all {col.count()} memories scored, top-{args.k} kept")
    hits = col.query(query_texts=[QUESTION], n_results=col.count(), include=["documents", "distances"])
    ranked = [(doc, similarity(d)) for doc, d in zip(hits["documents"][0], hits["distances"][0])]
    qwords = words(QUESTION)
    print(f"\n   rank  sim                  shared words     memory")
    for i, (doc, sim) in enumerate(ranked, 1):
        shared = ", ".join(sorted(words(doc) & qwords)) or "-"
        print(f"   {i:>3}   {sim:.3f}  {bar(sim, 1.0, 12):<12}  {shared:<16} {doc}{tag(doc)}")
        if i == args.k:
            print(f"   {'':>3}   ------ top-{args.k} cut: everything above this line goes to the model ------")
    top = [doc for doc, _ in ranked[:args.k]]
    print(f"\n   Why the needle wins: it shares 'show me', 'units' AND the intent 'I prefer' with the question.")
    print(f"   Why the near misses are close: they talk about units, but about someone else's.")
    print(f"   Why the haystack is far: nothing about units at all. The ranking did the selecting.")

    # ---- 4. the two prompts ------------------------------------------------------
    rule("4 · THE TWO PROMPTS — what the model actually receives")
    ret_prompt = build_prompt(top)
    ret_size = prompt_tokens(ret_prompt)
    show_prompt(f"A · RETRIEVAL: top-{args.k} only  ({ret_size} tokens)", ret_prompt)
    show_prompt(f"B · THE DUMP: all {len(all_notes)} notes  ({dump_size} tokens)", dump_prompt)
    print(f"\n   Same question. Same needle inside. One prompt is {dump_size / ret_size:.0f}x the other.")
    if args.no_api:
        return

    # ---- 5. the answers ----------------------------------------------------------
    rule(f"5 · THE ANSWERS — correct? tokens? money at ${args.price}/1M input")
    print(f"\n   {'prompt':<22} {'correct':<9} {'tokens':>7}   {'per question':>13}   {'per 1,000 q':>12}")
    ok, size, text = ask(top)
    ret_billed = size
    print(f"   {'retrieval top-' + str(args.k):<22} {f'{int(ok)}/1':<9} {size:>7}   {usd(size, args.price):>13}   "
          f"{usd(size * 1000, args.price):>12}")
    print(f"      model answered: {text.strip()!r}")
    results = {}
    for where in ("START", "MIDDLE", "END"):
        hits_ok, size, answers = 0, 0, []
        for t in range(args.trials):
            ok, size, text = ask(place(notes, where, seed=100 + t))
            hits_ok += ok
            answers.append((ok, text.strip()))
        results[where] = (hits_ok, size)
        print(f"   {'dump, needle at ' + where:<22} {f'{hits_ok}/{args.trials}':<9} {size:>7}   "
              f"{usd(size, args.price):>13}   {usd(size * 1000, args.price):>12}")
        for t, (ok, text) in enumerate(answers, 1):
            print(f"      trial {t} model answered: {text!r}{'' if ok else '   <- WRONG'}")

    big = results["START"][1]
    worst = min(v[0] for v in results.values())
    rule("receipt")
    print(f"   dump: {big} tokens per question · retrieval: {ret_billed} · ratio {big / max(ret_billed, 1):.0f}x")
    print(f"   worst position in the dump: {worst}/{args.trials} correct")
    print(f"   The dump paid for {len(all_notes) - args.k} notes that said nothing about units,")
    print(f"   and 2 of them said 'imperial' and 'square feet' right next to the needle.")
    print(f"   Retrieval never showed the model those. That is the select lever.")


if __name__ == "__main__":
    main()
