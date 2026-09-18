"""
Module 6 Lab — STARTER
Personal Knowledge Assistant: short-term (summarized) + long-term (persistent vector) memory.

Part 1: conversation buffer + summarization.
Part 2: vector write/read paths, persistence across restart, citations.

Fill in the TODOs. Each TODO names the worksheet step it belongs to.

Install (into the SAME venv as Modules 1-5, Python 3.12):
    Module-02\\.venv\\Scripts\\python.exe -m pip install -r Module-06\\requirements.txt
Check:
    Module-02\\.venv\\Scripts\\python.exe Module-06\\m6_preflight.py
Run (two SEPARATE processes — that is the whole point of Part 2):
    python memory_agent.py --run1
    python memory_agent.py --run2

Your key lives in the repo-root .env (OPENROUTER_API_KEY=sk-or-...), same as M1-M5.
"""

import argparse
import datetime
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
# from langchain_openai import ChatOpenAI
# import chromadb   # PersistentClient + BUILT-IN embeddings (all-MiniLM-L6-v2 via ONNX): no key, no torch

# Windows consoles default to cp1252 and turn every em-dash into mojibake.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = Path(__file__).resolve().parent
load_dotenv(HERE.parent.parent / ".env")      # repo-root .env

SUMMARIZE_AFTER_TURNS = 6
KEEP_LAST = 4
TOP_K = 3
DB_DIR = HERE / "memory_store"   # MUST persist to disk for cross-restart recall.
                                 # Next to THIS FILE, not the current directory — a cwd-relative
                                 # path is the #1 cause of "it forgot everything after restart".

# llm = ChatOpenAI(
#     model=os.getenv("MODEL", "openai/gpt-4o-mini"), temperature=0,
#     base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
#     api_key=os.environ["OPENROUTER_API_KEY"],
# )
# client = chromadb.PersistentClient(path=str(DB_DIR))
# collection = client.get_or_create_collection("memories", metadata={"hnsw:space": "cosine"})
#   ^ no embedding_function argument = chromadb's built-in local model
#   ^ cosine space, so  similarity = 1 - distance  (0 = unrelated, 1 = identical)


# ---------------------------------------------------------------------------
# SHORT-TERM MEMORY
# ---------------------------------------------------------------------------
class ShortTermMemory:
    def __init__(self):
        self.buffer = []      # recent turns, verbatim
        self.summary = ""     # rolling summary of older turns

    def add(self, role: str, text: str):
        self.buffer.append({"role": role, "text": text})
        # TODO (Steps 2-3): if len(self.buffer) > SUMMARIZE_AFTER_TURNS -> summarize the OLDER
        # turns with one LLM call, fold them into self.summary, keep only the last KEEP_LAST verbatim.
        # Print a one-line receipt when it fires, so you can SEE it in Step 5.
        raise NotImplementedError

    def context(self) -> str:
        # TODO (Step 4): return summary + recent turns as ONE bounded context string.
        raise NotImplementedError


# ---------------------------------------------------------------------------
# LONG-TERM MEMORY (persistent vector store)
# ---------------------------------------------------------------------------
def should_remember(text: str) -> bool:
    # TODO (Step 6, WRITE policy): store durable preferences/facts about the user, not every line.
    # A few regexes are enough ("I prefer", "I'm researching", "my project" ...).
    raise NotImplementedError


def write_memory(text: str, mem_type: str = "fact"):
    # TODO (Step 6): collection.upsert(...) with metadata {text, source, timestamp, type}.
    # chromadb embeds the text for you. It is on disk the moment upsert returns.
    raise NotImplementedError


def recall(query: str, k: int = TOP_K) -> list:
    # TODO (Step 7): collection.query(query_texts=[query], n_results=k, include=[...])
    # -> return the top-k memories WITH their metadata (you need type + timestamp to cite).
    raise NotImplementedError


# ---------------------------------------------------------------------------
# AGENT TURN
# ---------------------------------------------------------------------------
def answer(user_text: str, stm: ShortTermMemory) -> str:
    # TODO: (a) write policy -> maybe write_memory;  (b) recall long-term memories;
    #       (c) build the context IN THIS ORDER: system rules -> recalled memories -> summary
    #           -> recent turns -> the question;
    #       (d) one LLM call; tell the model to CITE any memory it used as
    #           "(from your stored <type>, <YYYY-MM-DD>)"  (Step 9);
    #       (e) print a receipt: prompt size, how many memories were recalled;
    #       (f) stm.add(...) the user turn and the answer.
    raise NotImplementedError


# ---------------------------------------------------------------------------
# CLI — do not change; the worksheet's commands depend on these flags
# ---------------------------------------------------------------------------
RUN1 = "I prefer metric units and I'm researching renewable energy."
RUN2 = "Give me a quick figure for solar capacity."

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run1", action="store_true", help=f'send "{RUN1}"')
    ap.add_argument("--run2", action="store_true", help=f'send "{RUN2}" — in a NEW process')
    ap.add_argument("--chat", action="store_true", help="interactive; type quit to leave")
    args = ap.parse_args()

    stm = ShortTermMemory()
    print(f"[store: {DB_DIR}  pid: {os.getpid()}]")

    if args.run1:
        print(answer(RUN1, stm))
    elif args.run2:
        print(answer(RUN2, stm))
    elif args.chat:
        while (user := input("\nyou > ").strip().lower()) not in {"quit", "exit", "q"}:
            if user:
                print("\nassistant > " + answer(user, stm))
    else:
        ap.print_help()
