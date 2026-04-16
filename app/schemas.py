"""Request/response schemas."""

from pydantic import BaseModel, Field


class NewsAnalysisRequest(BaseModel):
    text: str = Field(min_length=1)


class NewsAnalysisResponse(BaseModel):
    risk_level: str
    credibility_score: float
    inference_time_ms: float
    suspicious_words: list[str]
    reasoning: str
