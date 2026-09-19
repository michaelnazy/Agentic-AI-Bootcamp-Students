"""
2 · the meter — you pay for the area under the curve.

The same 12-turn conversation, run twice:
  naive       every turn resends the whole history          -> a ramp
  summarised  older turns folded into one rolling summary,  -> a sawtooth
              the last KEEP_LAST kept verbatim

    python 2_meter.py               # live: ~26 API calls, prompt sizes as billed
    python 2_meter.py --answers     # + print both agents' answers per turn, and the final summary
    python 2_meter.py --offline     # zero API calls: canned replies, tiktoken counts, 2 seconds

Line to land: "Naive is a ramp. Summarised is a sawtooth. You are billed for the
area under the curve — every turn, forever."
"""

from __future__ import annotations

import argparse

from _common import SYSTEM, bar, chat, messages_tokens, rule

SUMMARIZE_AFTER_TURNS = 6
KEEP_LAST = 4

TURNS = [
    "I'm researching renewable energy for a policy brief. Where should I start?",
    "Give me the global solar capacity figure for last year.",
    "And wind? Onshore and offshore separately if you can.",
    "Which three countries added the most solar capacity?",
    "Explain capacity factor in two sentences.",
    "How does that differ between solar and offshore wind?",
    "What is the levelised cost of electricity, briefly?",
    "Which is cheaper today per megawatt-hour, new solar or new gas?",
    "Summarise the main grid-storage options in one line each.",
    "What share of global electricity came from renewables last year?",
    "Give me one risk to the growth forecast that people underrate.",
    "Draft a two-sentence opening for my brief using what we discussed.",
]

# used only in --offline mode, so the numbers are deterministic and free
CANNED = [
    "Start with the IEA Renewables report and IRENA's capacity statistics; they are the standard references.",
    "Global installed solar PV capacity passed roughly 1,400 GW by the end of last year.",
    "Onshore wind is around 950 GW; offshore wind roughly 75 GW, growing faster in percentage terms.",
    "China by a wide margin, then the United States, then India.",
    "Capacity factor is actual output divided by the output if a plant ran at full power all year. It captures intermittency.",
    "Utility solar sits around 15-25 percent; offshore wind around 40-50 percent, because wind at sea is steadier.",
    "LCOE spreads all lifetime costs over all lifetime output, giving a cost per megawatt-hour for comparison.",
    "New utility solar is generally cheaper than new gas in most markets, before storage costs.",
    "Lithium-ion batteries: hours. Pumped hydro: hours to days. Green hydrogen: seasonal, still expensive.",
    "Roughly 30 percent of global electricity generation came from renewables last year.",
    "Grid connection queues: projects are built faster than transmission, so capacity waits idle.",
    "Renewables now supply about a third of the world's electricity, led by solar and wind. The binding constraint is no longer cost but the grid that carries it.",
]


def offline_respond(messages, i):
    return CANNED[i], messages_tokens(messages)


def live_respond(messages, i):
    return chat(messages)


def offline_summarise(summary, older):
    facts = "; ".join(" ".join(t.split()[:7]) for role, t in older if role == "user")
    return (summary + " " if summary else "") + f"Asked about: {facts}."


def live_summarise(summary, older):
    transcript = "\n".join(f"{r}: {t}" for r, t in older)
    text, _ = chat([("user", "Update the running summary of a conversation. Keep durable facts and "
                             f"open questions, max 80 words.\n\nCURRENT SUMMARY:\n{summary or '(none)'}"
                             f"\n\nNEW TURNS:\n{transcript}")])
    return text


def run_naive(respond):
    history, sizes, replies = [], [], []
    for i, user in enumerate(TURNS):
        history.append(("user", user))
        reply, size = respond([("system", SYSTEM)] + history, i)
        history.append(("assistant", reply))
        sizes.append(size)
        replies.append(reply)
    return sizes, replies


def run_summarised(respond, summarise):
    buffer, summary, sizes, fired, replies = [], "", [], [], []
    for i, user in enumerate(TURNS):
        messages = [("system", SYSTEM)]
        if summary:
            messages.append(("system", "SUMMARY OF EARLIER CONVERSATION:\n" + summary))
        messages += buffer + [("user", user)]
        reply, size = respond(messages, i)
        sizes.append(size)
        replies.append(reply)
        buffer += [("user", user), ("assistant", reply)]
        if len(buffer) > SUMMARIZE_AFTER_TURNS:
            older, buffer = buffer[:-KEEP_LAST], buffer[-KEEP_LAST:]
            summary = summarise(summary, older)
            fired.append(i + 1)
    return sizes, fired, replies, summary


def wrap(text: str, indent: int, width: int = 66) -> str:
    import textwrap
    pad = " " * indent
    return "\n".join(pad + line for line in textwrap.wrap(" ".join(text.split()), width))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="no API calls; canned replies + tiktoken")
    ap.add_argument("--answers", action="store_true", help="print both agents' answers per turn + final summary")
    args = ap.parse_args()
    respond = offline_respond if args.offline else live_respond
    summarise = offline_summarise if args.offline else live_summarise

    rule(f"the meter · {'OFFLINE (tiktoken)' if args.offline else 'LIVE (prompt size as billed)'}")
    naive, naive_replies = run_naive(respond)
    summ, fired, summ_replies, summary = run_summarised(respond, summarise)
    scale = max(naive)

    if args.answers:
        for i, (user, a, b) in enumerate(zip(TURNS, naive_replies, summ_replies), 1):
            rule(f"turn {i}")
            print(f'   > "{user}"')
            print(f"   NAIVE       ({naive[i - 1]} tokens in)")
            print(wrap(a, 6))
            print(f"   SUMMARISED  ({summ[i - 1]} tokens in)" + ("   <- fold after this turn" if i in fired else ""))
            print(wrap(b, 6))
        rule("the rolling summary at the end (what turns 1-8 became)")
        print(wrap(summary, 3))
        print()

    print(f"\n   turn   naive   summarised   naive ==== / summarised ####")
    for i, (n, s) in enumerate(zip(naive, summ), 1):
        flag = "  <- summarised here" if i in fired else ""
        print(f"   {i:>3}   {n:>6}   {s:>9}    {bar(n, scale, 34, '=')}")
        print(f"   {'':>3}   {'':>6}   {'':>9}    {bar(s, scale, 34, '#')}{flag}")

    total_n, total_s = sum(naive), sum(summ)
    rule("receipt")
    print(f"   area under the naive curve ........ {total_n:>6}")
    print(f"   area under the summarised curve ... {total_s:>6}")
    print(f"   saved ............................. {total_n - total_s:>6}   ({(1 - total_s / total_n) * 100:.0f}%)")
    print(f"   last-turn prompt: naive {naive[-1]} vs summarised {summ[-1]}")
    print(f"\n   12 turns. Imagine 120. The naive line keeps climbing; the sawtooth does not.")
    if not args.offline:
        print("   (the summariser's own calls are extra — small, and they happen once per fold, not per turn)")


if __name__ == "__main__":
    main()
