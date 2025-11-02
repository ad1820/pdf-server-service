from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class Message(BaseModel):
    role: str 
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class PDFMetadata(BaseModel):
    filename: str
    size_kb: Optional[float] = None
    num_pages: Optional[int] = None
    uploaded_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class Conversation(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    pdf_url: Optional[str] = None
    metadata: Optional[PDFMetadata] = None
    messages: List[Message] = []


class UserCreate(BaseModel):
    email: str
    password: str


class UserInDB(BaseModel):
    uid: str
    email: str
    auth_provider: str
    active_chat: bool = False
    cloudinary_pdf_link: Optional[str] = None
    conversations: List[Conversation] = []
