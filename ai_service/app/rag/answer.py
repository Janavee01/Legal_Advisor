"""
answer.py — Grounded answer generation over retrieval results.

Takes the top-k sections from retrieve() and asks a Google Gemini model
(native REST, no OpenRouter) to answer the user's query using ONLY the
provided statutory text, citing each claim as Act › Section.

The API key is read from GEMINI_API_KEY (falls back to API_KEY), loaded
from ~/.config/legal_advisor/.env if not already set in the environment.
"""

import os
import time
from pathlib import Path

import requests

from .retrieve import retrieve

PROJECT_ROOT = Path(__file__).resolve().parents[3]

GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
)

DEFAULT_MODEL = "gemini-3.6-flash"

DEFAULT_FALLBACK_MODELS = [
    "gemini-3.5-flash",
    "gemini-flash-latest",
]

MAX_SECTION_CHARS = 1200
DEFAULT_MAX_TOKENS = 8192

MAX_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = [5, 15, 30]

SYSTEM_PROMPT = (
    "You are a legal information assistant for Indian law. Answer the "
    "user's question using ONLY the statutory sections provided. Base every "
    "claim on the source text; if the provided sections do not answer the "
    "question, say so plainly. Cite each claim as \"Act, Section X\" using "
    "the section's act name and number. Do not invent sections, cases, or "
    "provisions that are not in the provided text. Write in clear, plain "
    "English.\n\n"
    "Structure your answer as:\n"
    "- A short one-line summary of the user's rights or situation.\n"
    "- The applicable legal provisions with their specific statutory limits, "
    "thresholds, fines, or time periods as stated in the provided text.\n"
    "- Practical steps the user can take (how to file a complaint, where to "
    "go, time limits to act).\n\n"
    "If any monetary amounts, fines, or thresholds appear in the source text, "
    "state the figure AND add a brief note that it may have been updated by "
    "subsequent amendments.\n\n"
    "You are not giving legal advice."
)

def _load_env():
    """Load the user's private .env file without overriding existing variables."""
    env_file = Path.home() / ".config" / "legal_advisor" / ".env"

    if not env_file.exists():
        return

    for line in env_file.read_text().splitlines():
        line = line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value

def _api_key():
    _load_env()
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("API_KEY", "").strip()

    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to "
            "~/.config/legal_advisor/.env or export it in the shell."
        )

    return key

def build_messages(query: str, results: list[dict]) -> tuple[str, str]:
    """Build (system_prompt, user_content) from the top-k retrieval results."""
    section_blocks = []

    for i, r in enumerate(results, start=1):
        title = (r.get("section_title") or "").strip()
        act = (r.get("act_name") or "").strip()
        section = (r.get("section_number") or "").strip()
        text = (r.get("text") or "").strip()

        if not text:
            continue

        if len(text) > MAX_SECTION_CHARS:
            text = text[:MAX_SECTION_CHARS] + " [truncated]"

        header = f"{act} › Section {section}"
        if title:
            header += f" — {title}"

        section_blocks.append(
            f"[{i}] {header}\n{text}"
        )

    user_prompt = (
        f"Question: {query}\n\n"
        "Relevant statutory sections:\n\n"
        + "\n\n---\n\n".join(section_blocks)
        + "\n\n"
        + "Based only on the sections above, answer the question and cite "
        + "the specific sections you rely on."
    )

    return SYSTEM_PROMPT, user_prompt


def _retry_delay(attempt: int) -> float:
    return RETRY_BACKOFF_SECONDS[min(attempt, len(RETRY_BACKOFF_SECONDS) - 1)]


def _call_gemini(
    model: str,
    system_prompt: str,
    user_prompt: str,
    key: str,
    max_tokens: int,
    temperature: float,
    timeout: float,
    assistant_text: str | None = None,
) -> requests.Response:
    """POST to Gemini generateContent with retry + backoff on 429/5xx.

    If `assistant_text` is given, it is appended as the model's previous
    turn and followed by a "continue" instruction, so a response that hit
    the token cap can be resumed instead of silently truncated.
    """
    url = f"{GEMINI_ENDPOINT}{model}:generateContent"

    contents = [{"role": "user", "parts": [{"text": user_prompt}]}]

    if assistant_text:
        contents.extend(
            [
                {"role": "model", "parts": [{"text": assistant_text}]},
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                "Your previous response hit the output "
                                "token limit and was cut off. Continue "
                                "exactly from where you stopped. Do not "
                                "repeat text already written above, do not "
                                "add a fresh headline or summary, and "
                                "finish the answer cleanly."
                            )
                        }
                    ],
                },
            ]
        )

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": contents,
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": temperature,
        },
    }

    headers = {
        "x-goog-api-key": key,
        "Content-Type": "application/json",
    }

    for attempt in range(MAX_ATTEMPTS):
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)

        if resp.status_code not in (429,) and resp.status_code < 500:
            return resp

        delay = _retry_delay(attempt)
        print(
            f"Gemini {resp.status_code} on "
            f"{model} — retrying in {delay:.0f}s "
            f"({attempt + 1}/{MAX_ATTEMPTS})"
        )
        time.sleep(delay)

    return resp


def generate_answer(
    query: str,
    results: list[dict],
    model: str | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    temperature: float = 0.2,
    timeout: float = 120.0,
    fallback_models: list[str] | None = None,
) -> dict:
    """Ask the LLM to answer `query` grounded in `results`.

    Tries `model` (default GEMINI_MODEL env or DEFAULT_MODEL) first, then
    each model in `fallback_models` (also a comma-separated
    GEMINI_FALLBACK_MODELS env var), retrying each on transient 429/5xx.

    Returns a dict with the generated answer, the model used, and the raw
    API usage. Raise RuntimeError if the key is missing or every model
    fails.
    """
    key = _api_key()

    if model is None:
        model = os.environ.get("GEMINI_MODEL") or DEFAULT_MODEL

    if fallback_models is None:
        env_fallbacks = os.environ.get("GEMINI_FALLBACK_MODELS", "")
        fallback_models = [
            m.strip()
            for m in env_fallbacks.split(",")
            if m.strip()
        ] or DEFAULT_FALLBACK_MODELS

    system_prompt, user_prompt = build_messages(query, results)

    last_resp = None

    for candidate in [model, *fallback_models]:
        resp = _call_gemini(
            candidate,
            system_prompt,
            user_prompt,
            key,
            max_tokens,
            temperature,
            timeout,
        )
        last_resp = resp

        if resp.status_code != 200:
            print(
                f"Model {candidate} failed ({resp.status_code}) — trying next"
            )
            continue

        data = resp.json()

        try:
            parts = data["candidates"][0]["content"]["parts"]
        except (KeyError, IndexError, TypeError):
            parts = []

        content = "".join(
            p.get("text", "") for p in parts if isinstance(p, dict)
        )

        finish_reason = data["candidates"][0].get("finishReason")

        if finish_reason == "MAX_TOKENS":
            if content.strip():
                print(
                    f"WARNING: {candidate} hit the max token limit — "
                    "resuming the answer"
                )
                resume = _call_gemini(
                    candidate,
                    system_prompt,
                    user_prompt,
                    key,
                    max_tokens,
                    temperature,
                    timeout,
                    assistant_text=content,
                )

                if resume.status_code == 200:
                    resume_data = resume.json()

                    try:
                        resume_parts = resume_data["candidates"][0][
                            "content"
                        ]["parts"]
                    except (KeyError, IndexError, TypeError):
                        resume_parts = []

                    continuation = "".join(
                        p.get("text", "")
                        for p in resume_parts
                        if isinstance(p, dict)
                    )

                    if continuation.strip():
                        content = f"{content}\n\n{continuation.strip()}"
                        finish_reason = resume_data["candidates"][0].get(
                            "finishReason"
                        )
                else:
                    print(
                        f"Resume failed for {candidate} "
                        f"({resume.status_code})"
                    )
            else:
                print(
                    f"WARNING: {candidate} hit the max token limit with "
                    "no output"
                )

        return {
            "answer": content,
            "model": candidate,
            "usage": data.get("usageMetadata") or {},
            "finish_reason": finish_reason,
        }

    raise RuntimeError(
        f"Gemini request failed ({last_resp.status_code}): "
        f"{last_resp.text[:500]}"
    )


def answer_from_results(
    query: str,
    results: list[dict],
    model: str | None = None,
    **gen_kwargs,
) -> dict:
    """Generate a grounded answer over an already-retrieved result list."""
    response = generate_answer(
        query,
        results,
        model=model,
        **gen_kwargs,
    )

    response["sources"] = [
        {
            "citation": r.get("citation"),
            "act_name": r.get("act_name"),
            "section_number": r.get("section_number"),
            "section_title": r.get("section_title"),
            "final_score": r.get("final_score"),
        }
        for r in results
    ]

    return response


def answer_retrieved(
    query: str,
    top_k: int = 5,
    category_filter: str | None = None,
    model: str | None = None,
    **retrieve_kwargs,
) -> dict:
    """Full pipeline: retrieve top-k, then generate a grounded answer."""
    retrieved = retrieve(
        query,
        top_k=top_k,
        category_filter=category_filter,
        **retrieve_kwargs,
    )

    return answer_from_results(query, retrieved["results"], model=model)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Ask a legal question and get a grounded, cited answer."
    )
    parser.add_argument("query", help="the question to answer")
    parser.add_argument(
        "--model",
        default=None,
        help="Gemini model id (default: "
        f"{DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="number of retrieval results to ground on",
    )
    args = parser.parse_args()

    out = answer_retrieved(
        args.query,
        top_k=args.top_k,
        model=args.model,
    )

    print("\n" + "=" * 70)
    print("ANSWER")
    print("=" * 70)
    print(out["answer"])
    print("\nSOURCES USED")
    for s in out["sources"]:
        print(f"  - {s['citation']} (score {s['final_score']:.3f})")