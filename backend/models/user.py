"""User model."""
from sqlalchemy import Column, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from models.base import Base, TimestampMixin, generate_uuid


class User(Base, TimestampMixin):
    """User table - includes organization info."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255))
    organization_name = Column(String(255))
    organization_nif = Column(String(50))
    role = Column(String(50), default="viewer")  # owner, admin, editor, viewer
    department = Column(String(255))  # User's department within the organization
    department_description = Column(Text)  # Description of the user's department

    # Relationships
    proposals = relationship("Proposal", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"
    
    def to_dict(self):
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "email": self.email,
            "name": self.name or self.email.split("@")[0].title(),
            "organization_name": self.organization_name,
            "organization_nif": self.organization_nif,
            "role": self.role or "viewer",
            "department": self.department,
            "department_description": self.department_description,
        }

