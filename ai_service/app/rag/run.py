from contextlib import redirect_stdout
import io
from ai_service.app.rag.retrieve import retrieve

queries = [
    "What happens if a child commits a crime in India?",
    "Can a minor be tried as an adult in serious cases?",
    "What is considered sexual harassment at workplace?",
    "Does POSH Act apply to contractual workers and interns?",
    "Who can file petition for child custody in court?",
    "possessing or carrying firearm without licence",
]

with open("hi.txt", "w", encoding="utf-8") as out:

    for q in queries:
        buffer = io.StringIO()

        # capture all prints from retrieve()
        with redirect_stdout(buffer):
            retrieve(q)

        logs = buffer.getvalue().splitlines()

        out.write("=" * 100 + "\n")
        out.write(f"QUERY: {q}\n")

        keep = False
        for line in logs:
            s = line.strip()

            if (
                s.startswith("MATCHED INTENTS:")
                or s.startswith("ANCHORS:")
            ):
                out.write(line + "\n")

            elif s.startswith("Top retrieval scores before rerank:"):
                keep = True
                out.write(line + "\n")
                continue

            elif keep:
                # stop when next section starts
                if (
                    s.startswith("Reranker scores:")
                    or s.startswith("Final Retrieval Results")
                ):
                    keep = False
                else:
                    out.write(line + "\n")

        out.write("\n\n")