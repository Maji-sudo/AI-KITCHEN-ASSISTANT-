from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.efficiency import EfficiencyScoreCreate, EfficiencyScoreResponse
from app.services.efficiency_service import efficiency_service

router = APIRouter(prefix="/efficiency", tags=["efficiency"])


@router.get("/{device_id}", response_model=List[EfficiencyScoreResponse])
def get_efficiency_scores(
    device_id: str,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the latest efficiency scores for a device."""
    return efficiency_service.get_latest_efficiency_scores(db, device_id=device_id, limit=limit)


@router.post("/", response_model=EfficiencyScoreResponse, status_code=201)
def compute_efficiency(
    body: EfficiencyScoreCreate,
    db: Session = Depends(get_db),
):
    """Store a newly computed efficiency score (called by the analytics job)."""
    return efficiency_service.compute_efficiency_score(db, score_in=body)
