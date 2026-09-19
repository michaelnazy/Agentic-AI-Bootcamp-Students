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
from langchain_openai import ChatOpenAI
import chromadb   # PersistentClient + BUILT-IN embeddings (all-MiniLM-L6-v2 via ONNX): no key, no torch

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

llm = ChatOpenAI(
    model=os.getenv("MODEL", "openai/gpt-4o-mini"), temperature=0,
    base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
    api_key=os.environ["OPENROUTER_API_KEY"],
)
client = chromadb.PersistentClient(path=str(DB_DIR))
collection = client.get_or_create_collection("memories", metadata={"hnsw:space": "cosine"})
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
        
        # Steps 2-3: The Trigger & The Summarize Node
        if len(self.buffer) > SUMMARIZE_AFTER_TURNS:
            print("   [trigger fired] folding older turns into summary...")
            
            # Slice the buffer: grab the oldest turns to fold, keep the rest verbatim
            older = self.buffer[:-KEEP_LAST]
            self.buffer = self.buffer[-KEEP_LAST:]
            
            # Ask the LLM to summarize the older turns
            transcript = "\n".join(f"{msg['role']}: {msg['text']}" for msg in older)
            prompt = (
                "Update the running summary of a conversation. Keep durable facts and open questions; max 80 words.\n\n"
                f"CURRENT SUMMARY:\n{self.summary or '(none)'}\n\n"
                f"NEW TURNS:\n{transcript}"
            )
            
            resp = llm.invoke([("user", prompt)])
            self.summary = resp.content.strip()

    def context(self) -> str:
        # Step 4: Return summary + recent turns as ONE bounded context string
        recent = "\n".join(f"{msg['role']}: {msg['text']}" for msg in self.buffer)
        if self.summary:
            return f"SUMMARY:\n{self.summary}\n\nRECENT TURNS:\n{recent}"
        return f"RECENT TURNS:\n{recent}"

# ---------------------------------------------------------------------------
# LONG-TERM MEMORY (persistent vector store)
# ---------------------------------------------------------------------------
import re
import hashlib
import time

def should_remember(text: str) -> str | None:
    # Step 6: WRITE policy. Store durable preferences/facts, not every line.
    if re.search(r"\b(i prefer|i like|i always|i never)\b", text, re.I):
        return "preference"
    if re.search(r"\b(i'm researching|my project|i work)\b", text, re.I):
        return "fact"
    return None

def write_memory(text: str, mem_type: str = "fact"):
    # Step 6: Write to chromadb with metadata
    mem_id = hashlib.sha256(text.lower().encode()).hexdigest()[:16] # create a unique ID
    collection.upsert(
        ids=[mem_id],
        documents=[text],
        metadatas=[{
            "type": mem_type, 
            "source": "user", 
            "timestamp": datetime.date.today().isoformat(), 
            "ts": time.time()
        }]
    )
    print(f"   [stored {mem_type}] {text}")

def recall(query: str, k: int = TOP_K) -> list:
    # Step 7: READ path. Retrieve top-k memories with their metadata
    if collection.count() == 0:
        return []
        
    hits = collection.query(
        query_texts=[query], 
        n_results=min(k, collection.count()), 
        include=["documents", "metadatas", "distances"]
    )
    
    recalled = []
    # Loop through the results (ChromaDB returns lists of lists)
    for doc, meta, dist in zip(hits["documents"][0], hits["metadatas"][0], hits["distances"][0]):
        similarity = round(1.0 - dist, 3)
        if similarity >= 0.2: # Only keep memories above a 0.2 similarity threshold
            recalled.append({
                "text": doc, 
                "type": meta["type"], 
                "timestamp": meta["timestamp"], 
                "sim": similarity
            })
    return recalled

# ---------------------------------------------------------------------------
# AGENT TURN
# ---------------------------------------------------------------------------
def answer(user_text: str, stm: ShortTermMemory) -> str:
    # (a) Check if we should write this to long-term memory
    # We split by "and" just in case the user says two things in one sentence
    for clause in re.split(r"\band\b", user_text, flags=re.I):
        clause = clause.strip()
        mem_type = should_remember(clause)
        if mem_type:
            write_memory(clause, mem_type)

    # (b) Recall long-term memories relevant to the user's text
    memories = recall(user_text)
    
    # Format the recalled memories for the prompt
    mem_block = ""
    if memories:
        mem_lines = [f"- [{m['type']}, {m['timestamp']}] {m['text']}" for m in memories]
        mem_block = "RECALLED MEMORIES:\n" + "\n".join(mem_lines) + "\n\n"

    # (c) Build the context in the exact right order (Rules -> Memories -> Summary -> Recent -> Question)
    messages = [
        ("system", "You are a helpful assistant. Treat every preference in RECALLED MEMORIES as an instruction. Cite each memory you apply exactly like this: (from your stored preference, 2026-09-19)."),
        ("system", f"{mem_block}CONTEXT:\n{stm.context()}"),
        ("user", user_text)
    ]
    
    # (d) Call the LLM
    resp = llm.invoke(messages)
    reply = resp.content.strip()
    
    # (e) Print the receipt
    prompt_size = resp.usage_metadata.get("input_tokens", 0)
    print(f"   [receipt] prompt size: {prompt_size} | memories recalled: {len(memories)}")
    
    # (f) Save to short-term memory
    stm.add("user", user_text)
    stm.add("assistant", reply)
    
    return reply
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