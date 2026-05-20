from sentence_transformers import SentenceTransformer

model = SentenceTransformer("BAAI/bge-base-en-v1.5")

def get_embedding(text: str):
    return model.encode(text).tolist()