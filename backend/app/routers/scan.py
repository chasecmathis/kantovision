from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, UploadFile
from pydantic import BaseModel

from app.config import get_settings
from app.dependencies import UserIdDep

logger = logging.getLogger(__name__)

router = APIRouter(tags=["scan"])


# ─── Response models ──────────────────────────────────────────────────────────


class PredictionOut(BaseModel):
    name: str
    confidence: float


class ClassifyResponse(BaseModel):
    predictions: list[PredictionOut]


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/scan/classify", response_model=ClassifyResponse)
def classify_image(file: UploadFile, _user: UserIdDep) -> ClassifyResponse:
    settings = get_settings()

    if not settings.classifier_enabled:
        raise HTTPException(status_code=503, detail="Classifier is not available")

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image (JPEG, PNG, or WebP)")

    contents = file.file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(contents) > max_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Image must be under {settings.max_upload_size_mb}MB",
        )

    from app.services.classifier import PokemonClassifier

    try:
        classifier = PokemonClassifier.get()
    except Exception:
        logger.exception("Failed to load classifier model")
        raise HTTPException(
            status_code=503, detail="Classifier model is loading, try again shortly"
        )

    try:
        predictions = classifier.predict(contents, top_k=5)
    except Exception:
        logger.exception("Inference failed")
        raise HTTPException(
            status_code=400, detail="Could not process image. Ensure it is a valid image file."
        )

    return ClassifyResponse(
        predictions=[PredictionOut(name=p.name, confidence=p.confidence) for p in predictions]
    )
