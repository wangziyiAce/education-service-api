"""普通 JWT 浏览器安全代理；任何服务端密钥都不会进入前端。"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from models.chat import CourseProject, EventLecture, EventRegistration, ChatMessage
from schemas.chat import ChatMessageCreate, ChatMessageResponse, ChatSessionCreate, ChatSessionResponse, CourseResponse, EventRegistrationCreate, EventResponse
from services.chat_service import create_or_get_session, get_owned_session, list_courses, list_events, save_message
from utils.auth import CurrentUser, get_current_user
from utils.database import get_db
from schemas.common import paginated_response, success_response

router = APIRouter(prefix="/api/v1/client", tags=["前端安全代理"])

@router.get("/courses")
def courses(page: int = 1, page_size: int = 20, keyword: str | None = None, category: str | None = None, _: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    items, total = list_courses(db, page, page_size, keyword, category); return paginated_response([CourseResponse.model_validate(x).model_dump() for x in items], total, page, page_size)

@router.get("/courses/{course_id}")
def course(course_id: int, _: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.get(CourseProject, course_id)
    if not item: raise HTTPException(404, "课程不存在")
    return success_response(CourseResponse.model_validate(item).model_dump())

@router.get("/events")
def events(page: int = 1, page_size: int = 20, status: str | None = "upcoming", _: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    items, total = list_events(db, page, page_size, status); return paginated_response([EventResponse.model_validate(x).model_dump() for x in items], total, page, page_size)

@router.get("/events/{event_id}")
def event(event_id: int, _: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.get(EventLecture, event_id)
    if not item: raise HTTPException(404, "活动不存在")
    return success_response(EventResponse.model_validate(item).model_dump())

@router.post("/events/{event_id}/register")
def register(event_id: int, data: EventRegistrationCreate, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if not db.get(EventLecture, event_id): raise HTTPException(404, "活动不存在")
    item = db.query(EventRegistration).filter_by(event_id=event_id, user_id=user.id).first()
    if item: item.status = "registered"; item.remark = data.remark
    else: item = EventRegistration(event_id=event_id, user_id=user.id, remark=data.remark); db.add(item)
    db.commit(); db.refresh(item); return success_response({"id": item.id, "event_id": event_id, "status": item.status})

@router.delete("/events/{event_id}/register")
def cancel(event_id: int, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(EventRegistration).filter_by(event_id=event_id, user_id=user.id).first()
    if not item: raise HTTPException(404, "报名记录不存在")
    item.status = "cancelled"; db.commit(); return success_response({"id": item.id, "status": item.status})

@router.post("/chat/sessions")
def create_session(_: ChatSessionCreate, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    return success_response(ChatSessionResponse.model_validate(create_or_get_session(db, user.id)).model_dump())

@router.get("/chat/sessions/{session_id}")
def session(session_id: str, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    item = get_owned_session(db, session_id, user.id)
    if not item: raise HTTPException(404, "会话不存在")
    return success_response(ChatSessionResponse.model_validate(item).model_dump())

@router.get("/chat/sessions/{session_id}/messages")
def messages(session_id: str, cursor: int | None = Query(None), limit: int = 20, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    if not get_owned_session(db, session_id, user.id): raise HTTPException(404, "会话不存在")
    query = db.query(ChatMessage).filter_by(session_id=session_id)
    if cursor: query = query.filter(ChatMessage.id < cursor)
    items = query.order_by(ChatMessage.id.desc()).limit(limit + 1).all(); has_more = len(items) > limit; items = items[:limit]
    return success_response({"items": [ChatMessageResponse.model_validate(x).model_dump() for x in reversed(items)], "next_cursor": items[-1].id if has_more and items else None, "has_more": has_more})

@router.post("/chat/sessions/{session_id}/messages")
def create_message(session_id: str, data: ChatMessageCreate, user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    item = get_owned_session(db, session_id, user.id)
    if not item: raise HTTPException(404, "会话不存在")
    return success_response(ChatMessageResponse.model_validate(save_message(db, item, data)).model_dump())
