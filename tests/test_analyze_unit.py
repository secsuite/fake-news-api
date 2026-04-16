"""Fast unit tests for analysis endpoint."""

from app.dependencies import get_predictor


class _StubPredictor:
    def analyze(self, text: str) -> dict[str, object]:
        assert text == "sample"
        return {
            "risk_level": "LOW RISK",
            "credibility_score": 88.5,
            "inference_time_ms": 9.3,
            "suspicious_words": ["urgent"],
            "reasoning": "Classifier confidence indicates mostly credible language patterns.",
        }


def test_analyze_news_uses_predictor_override(client):
    from app.main import app

    app.dependency_overrides[get_predictor] = lambda: _StubPredictor()
    response = client.post("/api/v1/analyze/news", json={"text": "sample"})
    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["risk_level"] == "LOW RISK"
    assert payload["credibility_score"] == 88.5
    assert payload["suspicious_words"] == ["urgent"]
