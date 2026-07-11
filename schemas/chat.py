"""课程、活动和安全会话 API 契约。"""
from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field


class CourseResponse(BaseModel):
    id: int; project_name: str; category: str | None = None; description: str | None = None
    target_audience: str | None = None; price: Decimal | None = None; duration: str | None = None
    tags: list[str] | None = None; status: int; create_time: datetime; update_time: datetime | None = None
    model_config = {"from_attributes": True}


class EventResponse(BaseModel):
    id: int; event_name: str; event_type: str; description: str | None = None; start_time: datetime
    end_time: datetime | None = None; location: str | None = None; max_participants: int | None = None
    current_participants: int; status: str; create_time: datetime
    model_config = {"from_attributes": True}


class EventRegistrationCreate(BaseModel):
    remark: str | None = Field(default=None, max_length=512)


class ChatSessionCreate(BaseModel):
    pass


class ChatSessionResponse(BaseModel):
    id: int; session_id: str; user_id: int; status: str; last_message_time: datetime | None = None; create_time: datetime
    model_config = {"from_attributes": True}


class ChatMessageCreate(BaseModel):
    role: Literal["user", "assistant", "system"] = "user"
    content: str = Field(min_length=1, max_length=10000)


class ChatMessageResponse(BaseModel):
    id: int; session_id: str; role: str; content: str; create_time: datetime
    model_config = {"from_attributes": True}
