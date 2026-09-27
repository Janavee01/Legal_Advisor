import os
os.environ["HF_HUB_OFFLINE"] = "1"

from sentence_transformers import SentenceTransformer
import torch

if torch.cuda.is_available():
    model = SentenceTransformer(
        "BAAI/bge-m3",
        model_kwargs={"torch_dtype": torch.float16},
    ).half()
else:
    model = SentenceTransformer("BAAI/bge-m3")

QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

_MODEL_GPU = None


def get_model():
    return model


def get_embedding(text: str, is_query: bool = False):
    if is_query:
        text = "Represent this sentence for searching relevant passages: " + text
    return model.encode(text, normalize_embeddings=True).tolist()


def free_gpu_for_rerank():
    """Move the embedder off the GPU and free its memory.

    The 3.6 GiB card cannot run the fp16 embedder and the fp16 reranker
    simultaneously for an 80-candidate pool without OOM, which sent every
    query down the slow CPU fallback. Free the embedder so the cross-encoder
    can run in larger GPU batches.
    """
    global model, _MODEL_GPU

    if not torch.cuda.is_available():
        return

    if _MODEL_GPU is None:
        on_cuda = str(next(model.parameters()).device).startswith("cuda")
        _MODEL_GPU = torch.cuda.current_device() if on_cuda else None

    if _MODEL_GPU is not None:
        model.to("cpu")
        torch.cuda.empty_cache()


def restore_embedder():
    """Move the embedder back to its original GPU after reranking."""
    global model, _MODEL_GPU

    if not torch.cuda.is_available() or _MODEL_GPU is None:
        return

    model.to(f"cuda:{_MODEL_GPU}")
    _MODEL_GPU = None