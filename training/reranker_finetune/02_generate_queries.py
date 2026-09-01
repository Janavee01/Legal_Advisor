import json
import os
import re
import sys
import time

from openai import OpenAI
from dotenv import load_dotenv

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../..")
)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

MODEL = "minimax/minimax-m3:free"
QUERIES_PER_SECTION = 4
MAX_TEXT_CHARS = 1500

PROMPT_TEMPLATE = """You are generating training data for an Indian legal RAG reranker.

Below is one section of an Indian statute. Generate {n} short, natural
questions that an ordinary person, NOT a lawyer, might type into a
legal-help chatbot where THIS section is the correct answer.

Rules:
- Use everyday language.
- Do not use legal jargon unless an ordinary person would naturally use it.
- Do not mention the section number.
- Do not quote the section title verbatim.
- Do not simply paraphrase the title.
- Make the questions genuinely different.
- Use different angles where appropriate:
  direct question, practical situation, "what happens if...", "can I...",
  "who is responsible...", "what are my rights/duties...", etc.
- The question must be answerable using THIS section alone.
- Every important fact needed to answer the question must appear in THIS section.
- Do not ask about procedures, fees, eligibility, penalties, rights, duties, or
  authorities unless THIS section specifically covers that topic.
- Do not generate a question merely because the topic is related to the Act.
- Do not rely on other sections of the Act to answer the question.
- If the section is narrow, keep the questions narrow and specific to its actual text.
- Do not invent facts, procedures, requirements, exceptions, or consequences.
- Do not introduce a specific country, person, place, amount, date, or hypothetical fact unless it appears in THIS section.
- Do not ask about enforcement, what authorities will do, or consequences unless THIS section explicitly states them.
- Do not ask whether something can be extended, renewed, appealed, challenged, or changed unless THIS section explicitly mentions it.
- Do not rely on another section of the Act to answer the question, even if THIS section refers to that section.
- Do not ask a question whose answer is contained in another section merely because THIS section mentions, incorporates, or refers to that section.
- If THIS section says "under section X", "as prescribed", "subject to section X", or otherwise refers to another provision, do not use the contents of that other provision when generating the question.
- Never ask about an action, remedy, extension, renewal, appeal, or consequence that is described only in a different section, even when that other section directly follows THIS section.
- Treat references such as "under section X", "as prescribed", or "the provisions of this Act shall apply" as references only; do not infer the contents of those provisions.
- A question is valid only if the complete answer can be obtained from the text provided under "Section text" alone.
- Output ONLY a JSON array containing exactly {n} strings.

Act: {act_name}
Section number: {section_number}
Section title: {section_title}

Section text:
{text}
"""


def clean_json_array(raw):
    raw = raw.strip()

    # Remove accidental markdown fences.
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw)

    # Extract the first JSON array if the model added extra text.
    start = raw.find("[")
    end = raw.rfind("]")

    if start >= 0 and end > start:
        raw = raw[start:end + 1]

    result = json.loads(raw)

    if not isinstance(result, list):
        raise ValueError("Model output was not a JSON array")

    return [
        x.strip()
        for x in result
        if isinstance(x, str) and x.strip()
    ]


def generate_for_section(client, chunk, n):
    prompt = PROMPT_TEMPLATE.format(
        n=n,
        act_name=chunk["act_name"],
        section_number=chunk["section_number"],
        section_title=chunk.get("section_title", ""),
        text=chunk.get("text", "")[:MAX_TEXT_CHARS],
    )

    for attempt in range(1, 5):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.3,
                max_tokens=1000,
            )

            print("MODEL USED:", response.model)

            raw = response.choices[0].message.content

            print("\n========== RAW MODEL RESPONSE ==========")
            print(repr(raw))
            print("========================================\n")

            if not raw:
                raise ValueError("Model returned empty content")

            queries = clean_json_array(raw)

            if len(queries) < n:
                raise ValueError(
                    f"Only got {len(queries)}/{n} queries"
                )

            return queries[:n]

        except Exception as e:
            print(
                f"  [warn] attempt {attempt}/4 failed: {e}"
            )

            if attempt < 4:
                delay = 2 ** (attempt - 1)
                print(f"  Retrying in {delay}s...")
                time.sleep(delay)

    return []

def main(hard_neg_path, out_path, limit=None):
    with open(hard_neg_path, "r", encoding="utf-8") as f:
        hard_negs = json.load(f)

    # Resume from an existing output file.
    if os.path.exists(out_path):
        with open(out_path, "r", encoding="utf-8") as f:
            out = json.load(f)

        print(f"Resuming: {len(out)} sections already completed.")
    else:
        out = {}

    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY not found. Add it to .env"
        )
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "http://localhost",
            "X-Title": "Legal Advisor Reranker Training",
        },
    )

    items = list(hard_negs.items())

    if limit is not None:
        items = items[:limit]

    total = len(items)

    for i, (key, entry) in enumerate(items, start=1):

        if key in out and len(out[key]) >= QUERIES_PER_SECTION:
            print(f"[{i}/{total}] {key}: already done")
            continue

        chunk = entry["chunk"]

        print(
            f"[{i}/{total}] Generating queries for "
            f"{chunk['act_name']} §{chunk['section_number']}..."
        )

        queries = generate_for_section(
            client,
            chunk,
            QUERIES_PER_SECTION,
        )

        out[key] = queries

        print(f"    Generated: {len(queries)} queries")

        # Checkpoint after every section.
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(
                out,
                f,
                indent=2,
                ensure_ascii=False,
            )

        # Small delay for rate limiting.
        time.sleep(0.5)

    print(f"\nDone. Written to {out_path}")


if __name__ == "__main__":
    if len(sys.argv) not in (3, 4):
        print(
            "Usage:\n"
            "  python 02_generate_queries.py "
            "<hard_negatives.json> <section_queries.json> [limit]"
        )
        sys.exit(1)

    hard_neg_path = sys.argv[1]
    out_path = sys.argv[2]

    limit = None

    if len(sys.argv) == 4:
        limit = int(sys.argv[3])

    main(
        hard_neg_path,
        out_path,
        limit,
    )