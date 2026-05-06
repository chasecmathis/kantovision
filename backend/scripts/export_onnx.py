"""Export the Pokemon classifier from HuggingFace to ONNX format.

Run once to generate the model files:
    uv run python scripts/export_onnx.py

Outputs:
    models/pokemon_classifier.onnx  — the ONNX model
    models/config.json              — label map + preprocessing params
"""

from __future__ import annotations

import json
from pathlib import Path

import torch
from transformers import ViTForImageClassification, ViTImageProcessor

MODEL_NAME = "imjeffhi/pokemon_classifier"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "models"


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)

    print(f"Downloading model: {MODEL_NAME}")
    processor = ViTImageProcessor.from_pretrained(MODEL_NAME)
    model = ViTForImageClassification.from_pretrained(MODEL_NAME)
    model.eval()

    # Export to ONNX
    dummy_input = torch.randn(1, 3, processor.size["height"], processor.size["width"])
    onnx_path = OUTPUT_DIR / "pokemon_classifier.onnx"

    print(f"Exporting to ONNX: {onnx_path}")
    torch.onnx.export(
        model,
        dummy_input,
        str(onnx_path),
        input_names=["pixel_values"],
        output_names=["logits"],
        dynamic_axes={"pixel_values": {0: "batch"}, "logits": {0: "batch"}},
        opset_version=14,
    )

    # Save config: labels + preprocessing params
    config = {
        "id2label": model.config.id2label,
        "image_size": processor.size["height"],
        "image_mean": processor.image_mean,
        "image_std": processor.image_std,
    }
    config_path = OUTPUT_DIR / "config.json"
    config_path.write_text(json.dumps(config, indent=2))

    onnx_size_mb = onnx_path.stat().st_size / (1024 * 1024)
    print(f"Done! Model: {onnx_size_mb:.1f} MB")
    print(f"Labels: {len(model.config.id2label)} classes")


if __name__ == "__main__":
    main()
