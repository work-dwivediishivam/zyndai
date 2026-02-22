"""ActiveTender model for storing published tenders."""
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from models.base import Base, TimestampMixin, generate_uuid


class ActiveTender(Base, TimestampMixin):
    """Active Tender table - stores published tenders extracted from proposals."""
    __tablename__ = "active_tenders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    proposal_id = Column(UUID(as_uuid=True), ForeignKey("proposals.id", ondelete="CASCADE"), nullable=False)
    
    # Required Fields
    title = Column(String(500), nullable=False)
    organization_nif = Column(String(50), nullable=False)
    price = Column(Integer, nullable=False, default=0)  # 0 if no price specified
    
    # Dates (auto-calculated on creation)
    submission_date = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    submission_deadline = Column(DateTime(timezone=True), nullable=False)  # submission_date + 1 week
    contract_expiry_date = Column(DateTime(timezone=True), nullable=False)  # submission_date + 1 year
    
    # Content
    tender_content = Column(Text, nullable=False)  # Full final draft markdown
    
    # Audit
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    def __repr__(self):
        return f"<ActiveTender {self.title}>"
    
    @staticmethod
    def calculate_dates(submission_date: datetime = None):
        """Calculate submission_deadline and contract_expiry_date from submission_date."""
        if submission_date is None:
            submission_date = datetime.utcnow()
        
        submission_deadline = submission_date + timedelta(weeks=1)
        contract_expiry_date = submission_date + timedelta(days=365)
        
        return {
            "submission_date": submission_date,
            "submission_deadline": submission_deadline,
            "contract_expiry_date": contract_expiry_date
        }
    
    def to_dict(self):
        """Convert to dictionary for API response."""
        return {
            "id": str(self.id),
            "proposal_id": str(self.proposal_id),
            "title": self.title,
            "organization_nif": self.organization_nif,
            "price": self.price,
            "submission_date": self.submission_date.isoformat() if self.submission_date else None,
            "submission_deadline": self.submission_deadline.isoformat() if self.submission_deadline else None,
            "contract_expiry_date": self.contract_expiry_date.isoformat() if self.contract_expiry_date else None,
            "tender_content": self.tender_content,
            "created_by": str(self.created_by),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
