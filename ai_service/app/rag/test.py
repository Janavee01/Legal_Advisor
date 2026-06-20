from ai_service.app.rag.retrieve import retrieve
from ai_service.app.rag.query_context_builder import QueryContextBuilder
import os
import logging

os.environ["TQDM_DISABLE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
TEST_QUERIES = [
    "sexual harassment at workplace remedy",
    "domestic violence protection orders",
    "wife harassed by husband legal remedy",
    "punishment for murder section 302",
    "bail conditions theft case",
    "defective product compensation injury",
    "refund for faulty appliance",
    "Can employer make worker work more than 9 hours?",
    "maximum working hours factory worker",
]


def run_debug_tests():
    builder = QueryContextBuilder()
    for query in TEST_QUERIES:
        print("\n" + "=" * 80)
        print("\nQUERY:", query)
        ctx = builder.build(query)

        print("\nCONTEXT")
        print("INTENTS:", ctx.intents)
        print("CONFIDENCE:", round(ctx.confidence, 4))
        print("ANCHORS:", ctx.anchors[:5])

        print("\nEXPANDED QUERY:")
        print(ctx.expanded_query[:300])

        #output = retrieve(query)

        #results = output["results"]

        #print("\nTOP RESULTS:")

        #for r in results[:5]:
         #   print(
          #      round(r.get("final_score", r["score"]), 4),
           #     r.get("citation"),
            #    r.get("section_title")
            #)

if __name__ == "__main__":
    run_debug_tests()

