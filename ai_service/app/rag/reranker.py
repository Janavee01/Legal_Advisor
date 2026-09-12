"""
reranker.py — Cross-encoder reranker.

Retrieval:
    BAAI/bge-m3

Reranking:
    BAAI/bge-reranker-v2-m3

The cross-encoder receives (query, legal-section) pairs and produces
the final relevance score used by retrieve.py.
"""

import numpy as np
import torch
from sentence_transformers import CrossEncoder


_reranker = None
_reranker_cpu = None

# ---------------------------------------------------------------------------
# Model path
# ---------------------------------------------------------------------------

RERANKER_MODEL_PATH = "BAAI/bge-reranker-v2-m3"


# Maximum characters of section text sent to the cross-encoder.
#
# Keep this at 600 for the first comparison so that the ONLY major
# experimental change is the reranker model itself.
MAX_TEXT_CHARS = 600

# ---------------------------------------------------------------------------
# Load reranker
# ---------------------------------------------------------------------------

def get_reranker() -> CrossEncoder:
    global _reranker

    if _reranker is None:
        device = (
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

        print(
            "Loading reranker:",
            RERANKER_MODEL_PATH,
        )

        # fp32 bge-reranker-v2-m3 (~2.3 GB) + fp16 bge-m3 (~1.1 GB) exceed
        # the ~3.6 GiB GPU budget, which forced every query into the slow
        # CPU fallback. Loading the reranker in fp16 keeps both models
        # resident on the GPU. (.half() on the CrossEncoder wrapper is not
        # supported, so dtype is set at construction time.)
        _reranker = CrossEncoder(
            RERANKER_MODEL_PATH,
            device=device,
            model_kwargs=(
                {"torch_dtype": torch.float16}
                if device == "cuda"
                else {}
            ),
        )

        print(
            "Reranker loaded on:",
            device,
        )

    return _reranker


def _get_cpu_reranker() -> CrossEncoder:
    global _reranker_cpu

    if _reranker_cpu is None:
        print(
            "Loading reranker fallback on:",
            "cpu",
        )

        _reranker_cpu = CrossEncoder(
            RERANKER_MODEL_PATH,
            device="cpu",
        )

    return _reranker_cpu


def _predict_reranker(
    pairs: list,
    batch_size: int = 32,
):
    """Run cross-encoder inference, falling back to CPU on CUDA OOM.

    The GPU (3.63 GiB) cannot always fit the reranker together with the
    embedding model; a few production queries blow past it. Rather than
    crash the whole retrieval, empty the CUDA cache and re-run the same
    inference on the CPU model (smaller batch to bound CPU memory).
    """
    model = get_reranker()

    if torch.cuda.is_available():
        # Free the embedding model's cached activations before cross-encoder
        # inference so the reranker can run on the GPU (CPU fallback is
        # roughly 10-60s per query on an 80-candidate pool).
        torch.cuda.empty_cache()

    try:
        return model.predict(
            pairs,
            batch_size=batch_size,
            show_progress_bar=False,
        )

    except (torch.cuda.OutOfMemoryError, RuntimeError) as exc:

        is_oom = (
            isinstance(exc, torch.cuda.OutOfMemoryError)
            or (
                isinstance(exc, RuntimeError)
                and "out of memory" in str(exc).lower()
            )
        )

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        if not is_oom:
            raise

        print(
            "Reranker CUDA out-of-memory — falling back to CPU"
        )

        return _get_cpu_reranker().predict(
            pairs,
            batch_size=min(batch_size, 16),
            show_progress_bar=False,
        )


# ---------------------------------------------------------------------------
# Rerank
# ---------------------------------------------------------------------------

_ANCHOR_SECTION_RE = None


def parse_anchor_keys(
    anchors: list[str],
) -> set:
    """Convert curated anchor strings to a set of (act, section) keys."""
    global _ANCHOR_SECTION_RE

    if not anchors:
        return set()

    if _ANCHOR_SECTION_RE is None:
        import re

        _ANCHOR_SECTION_RE = re.compile(
            r"(.*?)\s+Section\s+([0-9]+[A-Za-z]?)",
            re.IGNORECASE,
        )

    keys = set()

    for anchor in anchors:
        match = _ANCHOR_SECTION_RE.search(anchor)

        if not match:
            continue

        act = match.group(1).strip().lower()
        section = match.group(2).strip()

        if act and section:
            keys.add((act, section))

    return keys


def _anchor_tier(
    primary_keys: set | None,
    secondary_keys: set | None,
    act_name: str,
    section: str,
) -> str | None:
    """Return 'primary', 'secondary', or None for a candidate section."""
    if not primary_keys and not secondary_keys:
        return None

    act_lower = act_name.lower()
    section = str(section)

    for group, group_keys in (
        ("primary", primary_keys),
        ("secondary", secondary_keys),
    ):
        if not group_keys:
            continue

        for anchor_act, anchor_sec in group_keys:
            if anchor_sec == section and (
                anchor_act in act_lower
                or act_lower in anchor_act
            ):
                return group

    return None


def rerank(
    query: str,
    results: list[dict],
    primary_anchor_keys: set | None = None,
    secondary_anchor_keys: set | None = None,
) -> list[dict]:

    if not results:
        return results

    pairs = []
    valid_indices = []

    for i, result in enumerate(results):

        if not isinstance(result, dict):
            continue

        title = result.get(
            "section_title",
            "",
        )

        text = result.get(
            "text",
            "",
        )

        act = result.get(
            "act_name",
            "",
        )

        section = result.get(
            "section_number",
            "",
        )

        if not text:
            continue

        # ---------------------------------------------------------------
        # Keep the document representation identical to the previous
        # evaluation. This makes the model swap a clean A/B test.
        # ---------------------------------------------------------------

        text_truncated = (
            text[:MAX_TEXT_CHARS]
            + (
                " [truncated]"
                if len(text) > MAX_TEXT_CHARS
                else ""
            )
        )

        doc = (
            f"[TITLE] {title}. "
            f"[ACT] {act}. "
            f"[SECTION] {section}. "
            f"[TEXT] {text_truncated}"
        )

        pairs.append(
            (
                query,
                doc,
            )
        )

        valid_indices.append(i)

    if not pairs:
        return results

    # ---------------------------------------------------------------
    # Cross-encoder inference
    # ---------------------------------------------------------------

    raw_scores = _predict_reranker(
        pairs,
    )

    # ---------------------------------------------------------------
    # Normalize reranker scores to [0, 1]
    #
    # Min-max scaling turns a single candidate into a "winner" (1.0)
    # and everything else into ~0, letting one wrong cross-encoder pick
    # dominate the final blend. Rank-based scaling keeps the reranker's
    # ordering signal while giving every candidate a graded score, so a
    # single miscall can no longer win the whole ranking.
    # ---------------------------------------------------------------

    if len(raw_scores) > 1:

        order = raw_scores.argsort()[::-1]
        ranks = np.empty_like(
            raw_scores,
            dtype=float,
        )
        ranks[order] = np.arange(
            1,
            len(raw_scores) + 1,
            dtype=float,
        )

        normalized_scores = (
            len(raw_scores) - ranks + 1
        ) / len(raw_scores)

    else:
        normalized_scores = np.array(
            [1.0]
        )

    # ---------------------------------------------------------------
    # Attach scores
    # ---------------------------------------------------------------

    for idx, rerank_score, norm_score in zip(
        valid_indices,
        raw_scores,
        normalized_scores,
    ):

        result = results[idx]

        result["rerank_score"] = float(
            rerank_score
        )

        result["rerank_score_norm"] = float(
            norm_score
        )

        retrieval_score = float(
            result.get(
                "score",
                0.0,
            )
        )

        # -----------------------------------------------------------
        # Weak title signal
        # -----------------------------------------------------------

        title = result.get(
            "section_title",
            "",
        ).lower()

        query_tokens = set(
            query.lower().split()
        )

        title_tokens = set(
            title.split()
        )

        title_match = float(
            bool(
                query_tokens
                & title_tokens
            )
        )

        # -----------------------------------------------------------
        # Curated intent anchor signal
        #
        # Matched intents carry curated anchors that are the reliable
        # legal mapping for the query. The cross-encoder frequently
        # under-ranks the canonical section, so confirmed anchors get an
        # override on the final score and a pre-rerank boost (applied in
        # retrieve.py) for recall/pool membership. The first anchor of
        # the best-matching intent (primary) is heavily favored.
        # -----------------------------------------------------------

        tier = _anchor_tier(
            primary_anchor_keys,
            secondary_anchor_keys,
            result.get("act_name", ""),
            result.get("section_number", ""),
        )

        anchor_bonus = (
            0.45
            if tier == "primary"
            else 0.30
            if tier == "secondary"
            else 0.0
        )

        # -----------------------------------------------------------
        # Final score
        # -----------------------------------------------------------

        result["final_score"] = (
            0.55 * retrieval_score
            + 0.40 * float(norm_score)
            + 0.05 * title_match
            + anchor_bonus
        )

    # ---------------------------------------------------------------
    # Final ordering
    # ---------------------------------------------------------------

    return sorted(
        [
            result
            for result in results
            if isinstance(result, dict)
        ],
        key=lambda result: result.get(
            "final_score",
            0,
        ),
        reverse=True,
    )