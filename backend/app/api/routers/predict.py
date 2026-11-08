"""Prediction endpoint: ML-driven query difficulty, cost and strategy routing."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.ml.predictor import get_predictor
from app.schemas import PredictionSchema, PredictRequest, UserInfo
from app.security.auth import get_current_user
from app.security.sanitize import sanitize_user_query

router = APIRouter(tags=["predict"])


@router.post("/predict", response_model=PredictionSchema)
def predict(
    body: PredictRequest,
    user: UserInfo = Depends(get_current_user),
) -> PredictionSchema:
    """Predict a query's difficulty, expected hops/cost and a recommended strategy."""
    clean = sanitize_user_query(body.query) or body.query
    prediction = get_predictor().predict(clean)
    return PredictionSchema(
        query=clean,
        difficulty=prediction.difficulty,
        difficulty_confidence=prediction.difficulty_confidence,
        class_probabilities=prediction.class_probabilities,
        predicted_hops=prediction.predicted_hops,
        predicted_cost_usd=prediction.predicted_cost_usd,
        recommended_strategy=prediction.recommended_strategy,
        features=prediction.features,
    )
