from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.recommendation import RecommendationCreate, RecommendationResponse
from app.services.recommendation_service import recommendation_service

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/", response_model=List[RecommendationResponse])
def get_my_recommendations(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return active recommendations for the authenticated user."""
    return recommendation_service.get_active_recommendations(db, user_id=int(current_user.id), skip=skip, limit=limit)


@router.post("/", response_model=RecommendationResponse, status_code=201)
def create_recommendation(
    body: RecommendationCreate,
    db: Session = Depends(get_db),
):
    """Create a recommendation (called by the AI/analytics engine)."""
    return recommendation_service.create_recommendation(db, rec_in=body)


@router.patch("/{rec_id}/dismiss", response_model=RecommendationResponse)
def dismiss_recommendation(
    rec_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = recommendation_service.dismiss_recommendation(db, rec_id=rec_id)
    if not result:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return result


@router.patch("/{rec_id}/act", response_model=RecommendationResponse)
def act_on_recommendation(
    rec_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = recommendation_service.act_on_recommendation(db, rec_id=rec_id)
    if not result:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return result
