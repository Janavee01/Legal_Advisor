import chromadb

CHROMA_PATH = "ai_service/app/data/chroma"
COLLECTION = "nyaya_legal_knowledge"

client = chromadb.PersistentClient(path=CHROMA_PATH)

print("CLIENT OK")

collection = client.get_collection(COLLECTION)

from collections import Counter

data = collection.get(include=["metadatas"])

counter = Counter()

for m in data["metadatas"]:
    counter[m["source"]] += 1

for act, count in sorted(counter.items()):
    print(f"{count:5}  {act}")