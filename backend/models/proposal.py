"""Proposal model."""
from sqlalchemy import Column, String, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from models.base import Base, TimestampMixin, generate_uuid


class Proposal(Base, TimestampMixin):
    """Proposal table - stores markdown content."""
    __tablename__ = "proposals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, default="")
    pinned = Column(Boolean, default=False)
    status = Column(String(50), default="draft")
    final_draft = Column(Boolean, default=False)
    proposal_revision = Column(Text)  # Final draft to be published as active tender
    assigned_to_email = Column(String(255))  # Email of user who can see this revision

    # Relationships
    user = relationship("User", back_populates="proposals")

    def __repr__(self):
        return f"<Proposal {self.title}>"
    
    def to_dict(self):
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "title": self.title,
            "content": self.content or "",
            "pinned": self.pinned,
            "status": self.status,
            "final_draft": self.final_draft,
            "proposal_revision": self.proposal_revision or "",
            "assigned_to_email": self.assigned_to_email,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

