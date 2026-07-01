from ai_service.app.rag.retrieve import get_collection

collection = get_collection()

results = collection.get(
    include=["metadatas"]
)



collection.query(
    query_texts=["how to file an RTI application"],
    n_results=20,
    where={"category": "rights"}
)