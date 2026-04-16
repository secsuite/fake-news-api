"""Prediction service for fake-news classification."""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

from app.config import settings


class FakeNewsPredictor:
    """Loads ONNX classifier and computes API response payload."""

    def __init__(self, model_dir: str | Path) -> None:
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self._pipeline = None

    def _build_pipeline(self) -> Any:
        try:
            from optimum.onnxruntime import ORTModelForSequenceClassification
            from transformers import AutoTokenizer, pipeline
        except ImportError as exc:  # pragma: no cover - integration/runtime dependency guard
            raise RuntimeError(
                "Training/inference dependencies are required for fake-news inference. "
                "Run 'make install-train'."
            ) from exc

        tokenizer = AutoTokenizer.from_pretrained(str(self.model_dir))
        model = ORTModelForSequenceClassification.from_pretrained(
            str(self.model_dir),
            file_name=settings.MODEL_ONNX_FILE,
            provider="CPUExecutionProvider",
        )
        return pipeline(
            "text-classification",
            model=model,
            tokenizer=tokenizer,
            device=-1,
            top_k=None,
        )

    @property
    def classifier(self) -> Any:
        if self._pipeline is None:
            self._pipeline = self._build_pipeline()
        return self._pipeline

    @staticmethod
    def _normalize_text(text: str) -> str:
        cleaned = re.sub(r"<[^>]+>", " ", str(text))
        return re.sub(r"\s+", " ", cleaned).strip()

    @staticmethod
    def _extract_suspicious_words(text: str, limit: int = 5) -> list[str]:
        keywords = {
            "shocking",
            "secret",
            "conspiracy",
            "hoax",
            "propaganda",
            "rigged",
            "fraud",
            "fake",
            "hidden",
            "urgent",
            "miracle",
            "exposed",
            "scandal",
        }
        tokens = [w.strip(".,!?\"'()[]{}:;").lower() for w in text.split()]
        highlights: list[str] = []
        for token in tokens:
            if token in keywords and token not in highlights:
                highlights.append(token)
            if len(highlights) >= limit:
                break
        return highlights

    @staticmethod
    def _risk_level(score: float) -> str:
        if score >= 70.0:
            return "LOW RISK"
        if score < 40.0:
            return "HIGH RISK"
        return "MEDIUM RISK"

    def analyze(self, text: str) -> dict[str, object]:
        cleaned = self._normalize_text(text)
        if not cleaned:
            raise ValueError("Please provide non-empty article text")

        started = time.perf_counter()
        outputs = self.classifier(
            cleaned,
            truncation=True,
            max_length=settings.INFERENCE_MAX_LENGTH,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000

        if isinstance(outputs[0], list):
            scores = outputs[0]
        else:
            scores = outputs

        fake_score = 0.0
        for item in scores:
            if str(item.get("label", "")).upper() == "LABEL_1":
                fake_score = float(item.get("score", 0.0))
                break

        fake_probability = max(0.0, min(100.0, fake_score * 100.0))
        credibility_score = round(100.0 - fake_probability, 1)
        risk_level = self._risk_level(credibility_score)
        suspicious_words = self._extract_suspicious_words(cleaned)

        if risk_level == "HIGH RISK":
            reasoning = "Classifier confidence indicates disinformation-like patterns."
        elif risk_level == "MEDIUM RISK":
            reasoning = "Classifier detected mixed credibility signals."
        else:
            reasoning = "Classifier confidence indicates mostly credible language patterns."

        return {
            "risk_level": risk_level,
            "credibility_score": credibility_score,
            "inference_time_ms": round(elapsed_ms, 2),
            "suspicious_words": suspicious_words,
            "reasoning": reasoning,
        }
