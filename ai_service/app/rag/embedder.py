from sentence_transformers import SentenceTransformer
import torch

model = SentenceTransformer(
    "BAAI/bge-base-en-v1.5",
    device="cpu"   # or "cuda" only if you have >8GB GPU
)

def get_model():
    return model

def get_embedding(text: str):
    return model.encode(text, normalize_embeddings=True).tolist()