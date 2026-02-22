"""
Chat data models for proposal conversations with file attachments.
"""
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class FileAttachment(BaseModel):
    """File attachment metadata and content"""
    id: str
    filename: str
    content_type: str
    size: int
    content: str  # Base64 encoded or text content
    extracted_text: Optional[str] = None  # For PDFs, DOCX, etc.
    

class ChatMessage(BaseModel):
    """Individual chat message in a conversation"""
    id: str
    proposal_id: str
    role: str  # "user" or "assistant"
    content: str
    attachments: List[FileAttachment] = []
    created_at: str
    tokens_used: Optional[int] = None


class ChatRequest(BaseModel):
    """Request to send a chat message"""
    message: str
    # Files will be handled separately via multipart form data


class ChatResponse(BaseModel):
    """Response from chat endpoint"""
    message: ChatMessage
    tokens_used: int
    model: str = "gemini-2.5-flash"
