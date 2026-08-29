"""
02_generate_queries.py

For every section that has hard negatives mined, generates a handful of
natural, layperson-style queries that a real user might type — matching
the register of your retrieval_test_cases.py (e.g. "what happens if
employer does not pay salary", not "explain section 15 of the Payment
of Wages Act").

Requires: pip install anthropic
          export ANTHROPIC_API_KEY=...

Input:  hard_negatives.json (output of 01_mine_hard_negatives.py)
Output: section_queries.json
        {
          "<act_name>||<section_number>": ["query 1", "query 2", "query 3"],
          ...
        }

Run this ONCE, cache the output — it costs API calls proportional to
your number of sections, not your number of test queries.
"""

import json
import re
import sys
import time

import anthropic

MODEL = "claude-sonnet-4-6"
QUERIES_PER_SECTION = 4

PROMPT_TEMPLATE = """You are generating training data for a legal RAG reranker.

Below is one section of an Indian statute. Write {n} short, natural questions
that an ordinary person (NOT a lawyer) might type into a legal-help chatbot,
where THIS section is the correct answer.

Rules:
- Everyday phrasing, like someone describing their situation or asking a
  practical question. Avoid legal jargon and avoid saying the section number.
- Do NOT mention "Section {section_number}" or quote the section's own title
  verbatim — that would make the task trivially easy.
- Make the {n} questions genuinely different from each other (different
  angles: a direct question, a "what happens if..." scenario, a "can I..."
  question, a "who is responsible for..." question, etc).
- Output ONLY a JSON array of {n} strings. No preamble, no markdown fences.

Act: {act_name}
Section: {section_number}
Section title: {section_title}
Section text:
{text}
"""


def clean_json_array(raw: str) -> list[str]:
    raw = raw.strip()
    raw = re.sub(r"^```(json)?", "", raw).strip()
    raw = re.sub(r"```$", "", raw).strip()
    return json.loads(raw)


def generate_for_section(client: anthropic.Anthropic, chunk: dict, n: int) -> list[str]:
    prompt = PROMPT_TEMPLATE.format(
        n=n,
        act_name=chunk["act_name"],
        section_number=chunk["section_number"],
        section_title=chunk.get("section_title", ""),
        text=chunk.get("text", "")[:1500],
    )
    resp = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = "".join(b.text for b in resp.content if b.type == "text")
    try:
        queries = clean_json_array(raw)
        return [q for q in queries if isinstance(q, str) and q.strip()][:n]
    except Exception as e:
        print(f"  [warn] failed to parse response for {chunk['act_name']} {chunk['section_number']}: {e}")
        return []


def main(hard_neg_path: str, out_path: str):
    with open(hard_neg_path, "r", encoding="utf-8") as f:
        hard_negs = json.load(f)

    client = anthropic.Anthropic()
    out = {}

    items = list(hard_negs.items())
    for i, (key, entry) in enumerate(items):
        chunk = entry["chunk"]
        queries = generate_for_section(client, chunk, QUERIES_PER_SECTION)
        out[key] = queries
        print(f"[{i+1}/{len(items)}] {key}: {len(queries)} queries")

        # gentle pacing to avoid rate limits
        time.sleep(0.3)

        # incremental checkpoint every 50 sections in case of interruption
        if (i + 1) % 50 == 0:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(out, f, indent=2, ensure_ascii=False)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"\nDone. Written to {out_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python 02_generate_queries.py <hard_negatives.json> <section_queries_out.json>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])