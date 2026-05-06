from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class Prediction:
    name: str
    confidence: float


class PokemonClassifier:
    _instance: PokemonClassifier | None = None
    _lock = threading.Lock()

    def __init__(self, model_dir: str) -> None:
        model_path = Path(model_dir)
        logger.info("Loading ONNX classifier from: %s", model_path)

        # Load config (labels + preprocessing params)
        config = json.loads((model_path / "config.json").read_text())
        self.id2label: dict[int, str] = {int(k): v for k, v in config["id2label"].items()}
        self.image_size: int = config["image_size"]
        self.image_mean: list[float] = config["image_mean"]
        self.image_std: list[float] = config["image_std"]

        # Load ONNX model
        onnx_file = model_path / "pokemon_classifier.onnx"
        self.session = ort.InferenceSession(
            str(onnx_file),
            providers=["CPUExecutionProvider"],
        )
        logger.info("ONNX classifier loaded (%d classes)", len(self.id2label))

    @classmethod
    def get(cls) -> PokemonClassifier:
        if cls._instance is not None:
            return cls._instance
        with cls._lock:
            if cls._instance is not None:
                return cls._instance
            settings = get_settings()
            cls._instance = cls(settings.classifier_model_dir)
            return cls._instance

    def _preprocess(self, image_bytes: bytes) -> np.ndarray:
        """Resize, normalize, and format image for ViT input."""
        img = Image.open(BytesIO(image_bytes)).convert("RGB")
        img = img.resize((self.image_size, self.image_size), Image.LANCZOS)

        # Convert to float32 [0, 1] then normalize
        arr = np.array(img, dtype=np.float32) / 255.0
        mean = np.array(self.image_mean, dtype=np.float32)
        std = np.array(self.image_std, dtype=np.float32)
        arr = (arr - mean) / std

        # HWC -> CHW, add batch dimension
        arr = arr.transpose(2, 0, 1)[np.newaxis, ...]
        return arr

    def predict(self, image_bytes: bytes, top_k: int = 5) -> list[Prediction]:
        pixel_values = self._preprocess(image_bytes)

        (logits,) = self.session.run(None, {"pixel_values": pixel_values})

        # Softmax
        exp = np.exp(logits[0] - logits[0].max())
        probs = exp / exp.sum()

        top_indices = probs.argsort()[::-1][:top_k]

        return [
            Prediction(
                name=self.id2label[int(idx)].lower(),
                confidence=round(float(probs[idx]), 4),
            )
            for idx in top_indices
        ]
