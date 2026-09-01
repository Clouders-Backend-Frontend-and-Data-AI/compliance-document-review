from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.notification import Notification

class NotificationService:
    """In-app notifications for Advisors and Officers"""

    @staticmethod
    def create_notification(
        db: Session,
        user_id: str,
        title: str,
        message: str,
        document_id: Optional[str] = None
    ) -> Notification:
        notif = Notification(
            user_id=user_id,
            document_id=document_id,
            title=title,
            message=message,
            is_read=False
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif

    @staticmethod
    def get_user_notifications(
        db: Session,
        user_id: str,
        unread_only: bool = False
    ) -> List[Notification]:
        query = db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read == False)
        return query.order_by(Notification.created_at.desc()).all()

    @staticmethod
    def get_unread_count(db: Session, user_id: str) -> int:
        return db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()

    @staticmethod
    def mark_as_read(db: Session, notification_id: str, user_id: str) -> Optional[Notification]:
        notif = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        if notif:
            notif.is_read = True
            db.commit()
            db.refresh(notif)
        return notif

    @staticmethod
    def mark_all_as_read(db: Session, user_id: str) -> int:
        count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({"is_read": True})
        db.commit()
        return count
