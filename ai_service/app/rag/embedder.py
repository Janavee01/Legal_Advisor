from sentence_transformers import SentenceTransformer
import torch

model = SentenceTransformer(
    "BAAI/bge-large-en-v1.5"
)

def get_model():
    return model

def get_embedding(text: str):
    return model.encode(text, normalize_embeddings=True).tolist()