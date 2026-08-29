from sentence_transformers import SentenceTransformer
import torch

# BAAI/bge-m3: multilingual, 1024-dim (same space size as bge-large-en-v1.5),
# with substantially better semantic alignment on paraphrase-style queries
# (offline eval: 18/40 miss targets in semantic top-5 vs 10/40 for the old
# English-only model). fp16 on GPU so it fits alongside the cross-encoder
# reranker in the ~3.6 GiB available.
if torch.cuda.is_available():
    model = SentenceTransformer(
        "BAAI/bge-m3",
        model_kwargs={"torch_dtype": torch.float16},
    ).half()
else:
    model = SentenceTransformer("BAAI/bge-m3")

QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

def get_model():
    return model

def get_embedding(text: str, is_query: bool = False):
    if is_query:
        text = "Represent this sentence for searching relevant passages: " + text
    return model.encode(text, normalize_embeddings=True).tolist()