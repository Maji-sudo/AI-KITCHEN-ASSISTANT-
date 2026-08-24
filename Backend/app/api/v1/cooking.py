from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.user import User

from app.schemas.cooking import (
    DishCreate,
    DishResponse,
    CookingHistoryCreate,
    CookingHistoryUpdate,
    CookingHistoryResponse,
    ChatRequest,
    ChatResponse,
)

from app.services.cooking_service import cooking_service


router = APIRouter(
    prefix="/cooking",
    tags=["cooking"],
)


# ============================================================
# DISH LIBRARY
# ============================================================

@router.get(
    "/dishes",
    response_model=List[DishResponse],
)
def list_dishes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Return the shared dish library.
    Public endpoint.
    """
    return cooking_service.get_all_dishes(
        db,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/dishes",
    response_model=DishResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_dish(
    body: DishCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Add a new dish to the dish library.
    Authentication required.
    """
    return cooking_service.add_dish(
        db,
        dish_in=body,
    )


# ============================================================
# COOKING HISTORY
# ============================================================

@router.get(
    "/history",
    response_model=List[CookingHistoryResponse],
)
def get_my_cooking_history(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get cooking history of the logged-in user.
    """
    return cooking_service.get_user_history(
        db,
        user_id=int(current_user.id),
        skip=skip,
        limit=limit,
    )


@router.post(
    "/history",
    response_model=CookingHistoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def log_cooking_session(
    body: CookingHistoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Record a cooking session for the logged-in user.
    """

    body.user_id = int(current_user.id)

    return cooking_service.record_cooking_session(
        db,
        session_in=body,
    )


@router.patch(
    "/history/{session_id}",
    response_model=CookingHistoryResponse,
)
def update_cooking_session(
    session_id: int,
    body: CookingHistoryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update an existing cooking session.
    """

    result = cooking_service.update_cooking_session(
        db,
        session_id=session_id,
        session_in=body,
    )

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Cooking session not found",
        )

    return result


# ============================================================
# AI COOKING CHAT
# ============================================================

@router.post(
    "/chat",
    response_model=ChatResponse,
)
def cooking_chat(
    body: ChatRequest,
):
    """
    AI Cooking Assistant.

    Authentication is intentionally disabled for this endpoint
    during development.
    """

    reply = cooking_service.get_chat_response(
        body.message
    )

    return ChatResponse(
        reply=reply
    )