"""Integration tests that exercise real ONNX model inference."""

from __future__ import annotations

import os

import pytest


@pytest.mark.integration
@pytest.mark.requires_integration_secret
def test_real_model_inference(client):
    text = os.environ["FAKE_NEWS_INTEGRATION_TEXT"]
    response = client.post("/api/v1/analyze/news", json={"text": text})

    assert response.status_code == 200
    payload = response.json()
    assert payload["risk_level"] in {"LOW RISK", "MEDIUM RISK", "HIGH RISK"}
    assert 0.0 <= payload["credibility_score"] <= 100.0
    assert payload["inference_time_ms"] >= 0.0
    assert isinstance(payload["suspicious_words"], list)
    assert isinstance(payload["reasoning"], str) and payload["reasoning"]
