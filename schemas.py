from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CategoryCreate(BaseModel):
    name: str


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class NoteCreate(BaseModel):
    title: str
    content: str
    category_id: int


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    category_id: int
    created_at: datetime


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category_id: Optional[int] = None
