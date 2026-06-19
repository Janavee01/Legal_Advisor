from ai_service.app.rag.retrieve import get_collection

collection = get_collection()

results = collection.get(
    include=["metadatas"]
)

for meta in results["metadatas"]:
    act = meta.get("act_name", "")

    if "Domestic Violence" in act:
        print(meta)
        break