"""
Module 6 — Preflight check.
Run this THE DAY BEFORE the session. It changes nothing in your project; it
only reports — and it triggers the one-time embedding-model download so that
does not happen during the lab on classroom wifi.

    Module-02\\.venv\\Scripts\\python.exe Module-06\\m6_preflight.py      (Windows)
    python m6_preflight.py                                              (macOS)

Checks, in order:
  1. Python 3.12/3.13 (chromadb has no wheels for 3.14 yet)
  2. the four packages from requirements.txt
  3. OPENROUTER_API_KEY in the repo-root .env
  4. chromadb: add two memories -> query -> the right one comes back
     (this downloads all-MiniLM-L6-v2 the first time, ~80 MB)
  5. chromadb: the store PERSISTS — a second client on the same folder sees
     the same two memories (that is what the lab's restart depends on)
  6. one tiny LLM call through OpenRouter
"""

import importlib.metadata as md
import os
import shutil
import sys
import time
from pathlib import Path

# Windows consoles default to cp1252 and turn every em-dash into mojibake.
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
STORE = HERE / ".preflight_store"

TESTED = {
    "chromadb": "1.5.9",
    "langchain-openai": "1.4.1",
    "python-dotenv": "1.2.2",
    "tiktoken": "0.14.0",
}

OK, WARN, BAD = "[ OK ]", "[WARN]", "[FAIL]"
problems: list[str] = []


def main() -> int:
    print("=" * 62)
    print(" Agentic AI Bootcamp - Module 6 preflight")
    print("=" * 62)

    # 1. interpreter -------------------------------------------------------
    major, minor = sys.version_info[:2]
    version = f"{major}.{minor}.{sys.version_info[2]}"
    if (major, minor) in [(3, 12), (3, 13)]:
        print(f"{OK} Python {version}")
    elif (major, minor) >= (3, 14):
        print(f"{BAD} Python {version} - chromadb CANNOT install on 3.14 (no onnxruntime wheel).")
        problems.append(
            "Use the Module-02 venv (Python 3.12):\n"
            "       Module-02\\.venv\\Scripts\\python.exe Module-06\\m6_preflight.py"
        )
    else:
        print(f"{BAD} Python {version} - too old. Use 3.12 or 3.13.")
        problems.append("Install Python 3.12 and rebuild your venv.")

    in_venv = sys.prefix != sys.base_prefix
    print(f"{OK if in_venv else WARN} Virtual environment: "
          f"{'active' if in_venv else 'NOT active - you are using global Python'}")

    # 2. packages ----------------------------------------------------------
    print("-" * 62)
    missing = False
    for package, expected in TESTED.items():
        try:
            found = md.version(package)
        except md.PackageNotFoundError:
            print(f"{BAD} {package:<18} not installed")
            problems.append(f"pip install -r Module-06/requirements.txt  (missing {package})")
            missing = True
            continue
        flag = OK if found == expected else WARN
        note = "" if found == expected else f"  (class tested on {expected})"
        print(f"{flag} {package:<18} {found}{note}")
    if missing:
        return finish()

    # 3. key ---------------------------------------------------------------
    print("-" * 62)
    from dotenv import load_dotenv
    load_dotenv(REPO / ".env")
    key = os.environ.get("OPENROUTER_API_KEY", "")
    # report presence only; never echo the value or any part of it
    env_path = REPO / ".env"
    var = "OPENROUTER_API_KEY"
    if key.startswith("sk-or-"):
        print(f"{OK} .env: OpenRouter access configured ({env_path})")
    elif key:
        print(f"{WARN} .env: {var} is set but does not look like an OpenRouter value (sk-or-...)")
    else:
        print(f"{BAD} .env: {var} missing")
        problems.append(f"Put {var}=sk-or-... in {env_path} (same as Module 1-5).")

    # 4 + 5. chromadb round trip and persistence -----------------------------
    print("-" * 62)
    shutil.rmtree(STORE, ignore_errors=True)
    try:
        import chromadb

        t0 = time.time()
        client = chromadb.PersistentClient(path=str(STORE))
        col = client.get_or_create_collection("preflight", metadata={"hnsw:space": "cosine"})
        col.add(
            ids=["a", "b"],
            documents=["I prefer metric units", "The meeting is on Thursday"],
            metadatas=[{"type": "preference"}, {"type": "episodic"}],
        )
        secs = time.time() - t0
        hit = col.query(query_texts=["which units should I use?"], n_results=1)
        top = hit["documents"][0][0]
        dist = hit["distances"][0][0]
        if "metric" in top:
            print(f"{OK} chromadb embed -> store -> query   ({secs:.1f}s"
                  f"{', includes the one-time model download' if secs > 5 else ''})")
            print(f"{OK} nearest memory: '{top}'  distance {dist:.3f} (cosine, so 0 = identical)")
        else:
            print(f"{BAD} chromadb query returned '{top}' - expected the metric preference")
            problems.append("Delete Module-06/.preflight_store and re-run.")

        cache = Path.home() / ".cache" / "chroma" / "onnx_models" / "all-MiniLM-L6-v2"
        print(f"{OK if cache.exists() else WARN} embedding model cached at {cache}")

        # a SECOND client on the same folder = what a restart looks like
        del col, client
        client2 = chromadb.PersistentClient(path=str(STORE))
        n = client2.get_or_create_collection("preflight").count()
        if n == 2:
            print(f"{OK} persistence: a fresh client on the same folder sees {n} memories")
        else:
            print(f"{BAD} persistence: fresh client sees {n} memories, expected 2")
            problems.append("The store did not persist. Check you are not on a network/OneDrive folder.")
    except Exception as exc:
        print(f"{BAD} chromadb failed: {type(exc).__name__}: {exc}")
        problems.append("chromadb did not work - reinstall inside the venv (Python 3.12).")
    finally:
        shutil.rmtree(STORE, ignore_errors=True)

    # 6. one LLM call ---------------------------------------------------------
    print("-" * 62)
    if key:
        try:
            from langchain_openai import ChatOpenAI

            model = os.getenv("MODEL", "openai/gpt-4o-mini")
            llm = ChatOpenAI(
                model=model, temperature=0, max_tokens=5,
                base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
                api_key=key,
            )
            resp = llm.invoke("Reply with the single word: ready")
            usage = (resp.usage_metadata or {}).get("input_tokens", "?")
            ok_word = "ready" in resp.content.lower()
            size = f"prompt size {usage}"
            print(f"{OK if ok_word else WARN} LLM reachable: {model} ({size})")
        except Exception as exc:
            print(f"{BAD} LLM call failed: {type(exc).__name__}: {str(exc)[:160]}")
            problems.append("LLM call failed - check the key, or set MODEL=openai/gpt-4.1-mini in .env.")
    else:
        print(f"{WARN} skipped the LLM call (.env not configured)")

    return finish()


def finish() -> int:
    print("=" * 62)
    if problems:
        print(f"{len(problems)} thing(s) to fix before the session:\n")
        for i, p in enumerate(problems, 1):
            print(f"  {i}. {p}")
        print("\nStuck? Post this whole output in the class channel.")
        return 1
    print("All clear. You are ready for Module 6.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
