"""
_common.py — the five things every Module 6 demo needs, in one place.

    llm() / chat()      one ChatOpenAI pointed at OpenRouter; chat() returns
                        (answer, prompt_tokens) so every demo can print a number
    count_tokens()      tiktoken, for the offline paths — no API call
    open_collection()   a chromadb PersistentClient under demos/demo_store/<name>/
                        with cosine distance and chromadb's BUILT-IN embeddings
                        (all-MiniLM-L6-v2 via ONNX: no torch, no second key)
    reset_store()       rm -rf that folder
    bar()               an ASCII bar for the terminal — no box-drawing characters,
                        because Windows consoles will mangle them

Nothing in here is clever. It exists so the four demo files read as demos.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv

# Windows consoles default to cp1252 and turn every em-dash into mojibake.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
STORE_ROOT = HERE / "demo_store"

load_dotenv(REPO / ".env")

MODEL = os.getenv("MODEL", "openai/gpt-4o-mini")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

SYSTEM = "You are a concise research assistant. Answer in at most 60 words."

# ---------------------------------------------------------------- LLM ----
_llm = None


def llm(temperature: float = 0.0):
    """One ChatOpenAI, created on first use so the no-API demos never touch it."""
    global _llm
    if _llm is None:
        from langchain_openai import ChatOpenAI

        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            sys.exit("OPENROUTER_API_KEY is not set. Put it in the repo-root .env (see README.md).")
        _llm = ChatOpenAI(model=MODEL, temperature=temperature, base_url=BASE_URL, api_key=api_key)
    return _llm


def chat(messages, temperature: float = 0.0) -> tuple[str, int]:
    """messages: a list of (role, text) tuples, roles 'system' | 'user' | 'assistant'.
    Returns (answer, prompt_tokens) — the prompt size as billed by the API."""
    resp = llm(temperature).invoke(messages)
    usage = resp.usage_metadata or {}
    return resp.content.strip(), int(usage.get("input_tokens", 0))


# ------------------------------------------------------------- tokens ----
_enc = None


def count_tokens(text: str) -> int:
    """Approximate prompt size without calling the API (o200k_base = GPT-4o family)."""
    global _enc
    if _enc is None:
        import tiktoken

        _enc = tiktoken.get_encoding("o200k_base")
    return len(_enc.encode(text))


def messages_tokens(messages) -> int:
    """Rough size of a whole message list: text plus ~4 framing tokens per message."""
    return sum(count_tokens(text) + 4 for _, text in messages)


# ------------------------------------------------------------- chroma ----
def open_collection(name: str, path: str | Path | None = None):
    """A persistent collection at demos/demo_store/<name>/ (or `path`).

    No embedding_function argument = chromadb's built-in ONNX MiniLM model.
    metadata hnsw:space=cosine so `1 - distance` is a similarity in [0, 1].
    """
    import chromadb

    store = Path(path) if path else STORE_ROOT / name
    client = chromadb.PersistentClient(path=str(store))
    return client.get_or_create_collection(name, metadata={"hnsw:space": "cosine"})


def reset_store(name: str) -> None:
    shutil.rmtree(STORE_ROOT / name, ignore_errors=True)


def similarity(distance: float) -> float:
    return round(1.0 - distance, 3)


# ------------------------------------------------------------ display ----
def bar(n: float, scale: float, width: int = 40, ch: str = "#") -> str:
    """`n` out of `scale`, as a bar `width` characters wide at most."""
    if scale <= 0:
        return ""
    return ch * max(0, min(width, round(n / scale * width)))


def rule(title: str = "", ch: str = "-", width: int = 70) -> None:
    if title:
        print(f"{ch * 3} {title} {ch * max(0, width - len(title) - 5)}")
    else:
        print(ch * width)
