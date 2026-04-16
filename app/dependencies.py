"""Dependency providers."""

from functools import lru_cache

from app.config import settings
from app.services.predictor import FakeNewsPredictor


@lru_cache(maxsize=1)
def get_predictor() -> FakeNewsPredictor:
    return FakeNewsPredictor(settings.MODEL_DIR)


def preload_models() -> None:
    _ = get_predictor().classifier
