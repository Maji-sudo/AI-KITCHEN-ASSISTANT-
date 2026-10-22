from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.notification import NotificationResponse, UnreadCountResponse
from app.services.notification_service import notification_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=List[NotificationResponse])
def get_my_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    filter: Optional[str] = Query(None, description="all | unread | safety | reminder"),
    unread_only: bool = Query(False, description="Filter for unread alerts only"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Return paginated notifications for the authenticated user.
    Supports filtering by category (safety, reminder, unread) and pagination.
    Synchronizes real-time device leaks, low cylinder refill reminders, and device offline events.
    """
    return notification_service.get_user_notifications(
        db,
        user_id=int(current_user.id),
        filter_type=filter,
        unread_only=unread_only,
        skip=skip,
        limit=limit,
    )


@router.get("/unread-count", response_model=UnreadCountResponse)
def get_unread_notification_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the total count of unread notifications for the active user badge."""
    count = notification_service.get_unread_count(db, user_id=int(current_user.id))
    return {"unread_count": count}


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a specific notification as read."""
    notif = notification_service.mark_as_read(
        db, notification_id=notification_id, user_id=int(current_user.id)
    )
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or access denied.",
        )
    return notif


@router.post("/read-all")
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all notifications for the authenticated user as read."""
    count = notification_service.mark_all_read(db, user_id=int(current_user.id))
    return {"message": "All notifications marked as read", "count": count}


@router.delete("/{notification_id}", status_code=status.HTTP_200_OK)
def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a single notification belonging to the authenticated user."""
    success = notification_service.delete_notification(
        db, notification_id=notification_id, user_id=int(current_user.id)
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found or access denied.",
        )
    return {"message": "Notification deleted successfully"}


@router.delete("/", status_code=status.HTTP_200_OK)
def clear_notifications(
    all: bool = Query(False, description="If true, clear all; otherwise clear only read alerts"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Clear notifications for the user (defaults to clearing read ones)."""
    count = notification_service.clear_notifications(
        db, user_id=int(current_user.id), only_read=not all
    )
    return {"message": f"Cleared {count} notifications", "count": count}
