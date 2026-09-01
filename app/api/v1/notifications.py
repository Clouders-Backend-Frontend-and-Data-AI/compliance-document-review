from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.notification import NotificationOut, NotificationSummary
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/notifications", tags=["In-App Notifications"])

@router.get("", response_model=NotificationSummary)
def get_user_notifications(
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get in-app notifications for the logged in user with unread counter.
    Advisors see document decision updates and reviewer comments here.
    """
    notifications = NotificationService.get_user_notifications(
        db=db,
        user_id=current_user.id,
        unread_only=unread_only
    )
    unread_count = NotificationService.get_unread_count(db=db, user_id=current_user.id)
    return {
        "unread_count": unread_count,
        "notifications": notifications
    }

@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_notification_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a specific notification as read"""
    notif = NotificationService.mark_as_read(db=db, notification_id=notification_id, user_id=current_user.id)
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found."
        )
    return notif

@router.post("/read-all", response_model=dict)
def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read for current user"""
    count = NotificationService.mark_all_as_read(db=db, user_id=current_user.id)
    return {"message": f"Marked {count} notifications as read"}
