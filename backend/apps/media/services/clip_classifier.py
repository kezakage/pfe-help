"""
Zero-shot image classification via CLIP.

Uses sentence-transformers' built-in CLIP wrapper (`clip-ViT-B-32`) so we
don't add a new ML dependency on top of what the chatbot already pulls in.
The model is loaded lazily on first use (heavy: ~600MB) and reused for all
subsequent calls within the same worker process.

Returns a ranked list of `(label, score)` pairs — the caller decides on
the cutoff. Scores are softmax probabilities over the candidate labels,
not absolute confidence.
"""
from __future__ import annotations

import logging
import threading
from io import BytesIO
from typing import IO

logger = logging.getLogger(__name__)

# Architectural / heritage labels relevant to Algerian patrimony.
# Mix of building types, periods, and decorative elements so the model can
# pick whatever signal is dominant in the photo.
HERITAGE_LABELS: list[str] = [
    # Religious buildings
    "mosquée",
    "minaret",
    "mausolée",
    "medersa",
    "zaouïa",
    # Defensive / civic
    "casbah",
    "citadelle",
    "remparts fortifiés",
    "palais",
    "fontaine publique",
    "hammam",
    # Settlements
    "médina",
    "ksar",
    "village berbère",
    "pentapole du M'Zab",
    # Ancient
    "ruines romaines",
    "colonne romaine antique",
    "amphithéâtre antique",
    "peinture rupestre préhistorique",
    "gravure rupestre du Tassili",
    # Style markers
    "architecture ottomane",
    "architecture coloniale française",
    "architecture berbère traditionnelle",
    "maison traditionnelle algérienne",
    "arc en fer à cheval",
    "céramique zellige",
    # Non-heritage fallback (keeps confidence calibrated)
    "paysage naturel",
    "objet quelconque",
]

_model = None
_label_embeddings = None
_lock = threading.Lock()


def _get_model():
    """Lazy-load the CLIP encoder (thread-safe double-checked locking)."""
    global _model, _label_embeddings
    if _model is not None:
        return _model, _label_embeddings
    with _lock:
        if _model is None:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading CLIP model 'clip-ViT-B-32' (first call)…")
            _model = SentenceTransformer("clip-ViT-B-32")
            # Pre-compute label embeddings once so each image only needs the image encode.
            _label_embeddings = _model.encode(
                HERITAGE_LABELS,
                convert_to_tensor=True,
                normalize_embeddings=True,
            )
            logger.info("CLIP model loaded with %d candidate labels.", len(HERITAGE_LABELS))
    return _model, _label_embeddings


def classify_image(
    image_source: IO[bytes] | bytes,
    *,
    top_k: int = 3,
    min_score: float = 0.10,
) -> list[dict]:
    """
    Run CLIP zero-shot over `HERITAGE_LABELS` and return the top-K matches
    above `min_score`. Returned items are dicts: `{"label": str, "score": float}`.

    `image_source` may be a binary file-like object or a `bytes` blob.
    """
    from PIL import Image
    from sentence_transformers import util as st_util

    if isinstance(image_source, (bytes, bytearray)):
        img = Image.open(BytesIO(image_source))
    else:
        img = Image.open(image_source)
    img = img.convert("RGB")

    model, label_embs = _get_model()
    image_emb = model.encode([img], convert_to_tensor=True, normalize_embeddings=True)

    # Cosine similarity → softmax to get a comparable probability distribution.
    sims = st_util.cos_sim(image_emb, label_embs)[0]  # shape: (n_labels,)
    # Temperature 100 mimics CLIP's logit_scale and produces peaky distributions.
    import torch
    probs = torch.softmax(sims * 100.0, dim=-1).cpu().tolist()

    ranked = sorted(
        (
            {"label": HERITAGE_LABELS[i], "score": round(float(p), 4)}
            for i, p in enumerate(probs)
        ),
        key=lambda x: x["score"],
        reverse=True,
    )
    return [r for r in ranked[:top_k] if r["score"] >= min_score]
