from ai_service.app.rag.retrieve import retrieve

TEST_QUERIES = [
    "Can employer make worker work more than 9 hours?",
    "maximum working hours factory worker",
    "sexual harassment at workplace remedy",
    "defective product compensation injury",
    "refund for faulty appliance",
    "domestic violence protection orders",
    "wife harassed by husband legal remedy",
    "punishment for murder section 302",
    "bail conditions theft case",
]


def run_debug_tests():
    for query in TEST_QUERIES:
        print("\n" + "=" * 80)
        print("\nQUERY:", query)

        output = retrieve(query)

        results = output["results"]

        print("\nTOP RESULTS:")

        for r in results[:5]:
            print(
                r.get("score"),
                r.get("citation"),
                r.get("section_title")
            )


if __name__ == "__main__":
    run_debug_tests()