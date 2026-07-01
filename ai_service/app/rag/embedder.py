from sentence_transformers import SentenceTransformer
import torch

model = SentenceTransformer(
    "BAAI/bge-large-en-v1.5"
)

def get_model():
    return model

def get_embedding(text: str, is_query: bool = False):
    if is_query:
        text = "Represent this sentence for searching relevant passages: " + text
    return model.encode(text, normalize_embeddings=True).tolist()