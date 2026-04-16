"""News analysis API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_predictor
from app.schemas import NewsAnalysisRequest, NewsAnalysisResponse
from app.services.predictor import FakeNewsPredictor

router = APIRouter(prefix="/api/v1", tags=["analysis"])


@router.post("/analyze/news", response_model=NewsAnalysisResponse)
async def analyze_news(
    request: NewsAnalysisRequest,
    predictor: Annotated[FakeNewsPredictor, Depends(get_predictor)],
) -> NewsAnalysisResponse:
    try:
        result = predictor.analyze(request.text)
        return NewsAnalysisResponse.model_validate(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - runtime protection
        raise HTTPException(status_code=500, detail=str(exc)) from exc
