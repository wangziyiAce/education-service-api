"""课程、活动与会话的最小业务服务。"""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import or_
from sqlalchemy.orm import Session
from models.chat import ChatMessage, ChatSession, CourseProject, EventLecture, EventRegistration
from schemas.chat import ChatMessageCreate


def list_courses(db: Session, page: int, page_size: int, keyword: str | None, category: str | None):
    query = db.query(CourseProject).filter(CourseProject.status == 1)
    if keyword: query = query.filter(or_(CourseProject.project_name.contains(keyword), CourseProject.description.contains(keyword)))
    if category: query = query.filter(CourseProject.category == category)
    return query.order_by(CourseProject.id.desc()).offset((page - 1) * page_size).limit(page_size).all(), query.count()


def list_events(db: Session, page: int, page_size: int, status: str | None):
    query = db.query(EventLecture)
    if status: query = query.filter(EventLecture.status == status)
    return query.order_by(EventLecture.start_time).offset((page - 1) * page_size).limit(page_size).all(), query.count()


def create_or_get_session(db: Session, user_id: int):
    session = db.query(ChatSession).filter_by(user_id=user_id, status="active").order_by(ChatSession.id.desc()).first()
    if not session:
        session = ChatSession(session_id=uuid4().hex, user_id=user_id)
        db.add(session); db.commit(); db.refresh(session)
    return session


def get_owned_session(db: Session, session_id: str, user_id: int):
    return db.query(ChatSession).filter_by(session_id=session_id, user_id=user_id).first()


def save_message(db: Session, session: ChatSession, data: ChatMessageCreate):
    message = ChatMessage(session_id=session.session_id, role=data.role, content=data.content)
    session.last_message_time = datetime.utcnow(); db.add(message); db.commit(); db.refresh(message)
    return message
