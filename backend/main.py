"""
Uniflow Backend - FastAPI server with Supabase PostgreSQL.
"""
import os
import jwt
import uuid
from io import BytesIO
from typing import Optional, List
from datetime import datetime, timedelta

from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

# Import database and models
from database import get_db, init_db
from models import User, Proposal, ActiveTender

# Import services
from services.gemini_service import GeminiService
from services.file_processor import FileProcessor
from services.proposal_revision_service import ProposalRevisionService
from services.email_service import EmailService
from services.active_tender_service import ActiveTenderService
from models.chat import ChatMessage, FileAttachment

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage (runtime only - not persisted)
chat_history_db: dict[str, List[dict]] = {}
attachments_db: dict[str, dict] = {}

# Initialize Gemini service
try:
    gemini_service = GeminiService()
    print("✓ Gemini service initialized successfully")
except Exception as e:
    print(f"⚠ Warning: Gemini service initialization failed: {e}")
    gemini_service = None

# Initialize Proposal Revision service
try:
    proposal_revision_service = ProposalRevisionService()
    print("✓ Proposal Revision service initialized successfully")
except Exception as e:
    print(f"⚠ Warning: Proposal Revision service initialization failed: {e}")
    proposal_revision_service = None

# Initialize Email service
try:
    email_service = EmailService()
    print("✓ Email service initialized successfully")
except Exception as e:
    print(f"⚠ Warning: Email service initialization failed: {e}")
    email_service = None

# Initialize Active Tender service
try:
    active_tender_service = ActiveTenderService()
    print("✓ Active Tender service initialized successfully")
except Exception as e:
    print(f"⚠ Warning: Active Tender service initialization failed: {e}")
    active_tender_service = None

# Initialize database on startup
@app.on_event("startup")
async def startup():
    init_db()
    print("✓ Database tables initialized")


# --- Schemas ---
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProposalCreate(BaseModel):
    title: str
    content: str = ""


class ProposalIterate(BaseModel):
    user_input: str


class ProposalRename(BaseModel):
    title: str


class MemberAdd(BaseModel):
    email: str
    role: str


# --- Auth Schemas ---
class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str
    organization_name: str = ""
    organization_nif: str = ""
    department: str = ""


# --- Auth ---
def create_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=24)
    return jwt.encode({"sub": email, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user_email(authorization: str = None) -> str:
    """Extract email from JWT token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Handle "Bearer <token>" format
        if authorization.startswith("Bearer "):
            token = authorization[7:]
        else:
            token = authorization
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


from fastapi import Header

def get_current_user(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    email = get_current_user_email(authorization)
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user


@app.post("/auth/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    # Check if user already exists
    existing = db.query(User).filter(User.email == request.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Determine role based on organization
    # If organization already has users, new user is viewer
    # If organization is new, user is owner
    role = "viewer"
    if request.organization_name:
        existing_org_users = db.query(User).filter(
            User.organization_name == request.organization_name
        ).count()
        if existing_org_users == 0:
            role = "owner"  # First user in organization becomes owner
    else:
        role = "owner"  # Users without organization are owners by default
    
    # Create new user
    user = User(
        email=request.email,
        password_hash=request.password,  # In production, hash this!
        name=request.name,
        organization_name=request.organization_name,
        organization_nif=request.organization_nif,
        role=role,
        department=request.department
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return TokenResponse(access_token=create_token(request.email))


@app.post("/auth/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or user.password_hash != request.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=create_token(request.email))



# --- Proposals ---
@app.get("/proposals")
async def list_proposals(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    proposals = db.query(Proposal).filter(Proposal.user_id == user.id).all()
    return [p.to_dict() for p in proposals]


@app.post("/proposals")
async def create_proposal(data: ProposalCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    proposal = Proposal(
        user_id=user.id,
        title=data.title,
        content=data.content
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal.to_dict()


@app.get("/proposals/{proposal_id}")
async def get_proposal(proposal_id: str, db: Session = Depends(get_db)):
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return proposal.to_dict()


@app.post("/proposals/{proposal_id}/iterate")
async def iterate_proposal(
    proposal_id: str, 
    data: ProposalIterate, 
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Iterate on a proposal with Gemini AI.
    
    Each iteration completely replaces the proposal content with the AI-generated
    Draft Proposal. No chat history is maintained - the entire document is regenerated
    based on the user's instruction and the current content.
    """
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    if not gemini_service:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    try:
        # For assigned revisions, get department context from the assigned user
        assigned_department = None
        assigned_department_description = None
        
        if proposal.assigned_to_email:
            # This is a revision - look up the assigned user's department info
            assigned_user = db.query(User).filter(User.email == proposal.assigned_to_email).first()
            if assigned_user:
                assigned_department = assigned_user.department
                assigned_department_description = assigned_user.department_description
        
        # For revisions, use the proposal_revision content instead of content
        current_content = proposal.proposal_revision if proposal.assigned_to_email and proposal.proposal_revision else proposal.content
        
        # Generate updated proposal - this REPLACES the entire content
        # Pass user info from Supabase for the "Prepared By" field
        new_content = gemini_service.generate_proposal_response(
            user_message=data.user_input,
            current_content=current_content or "",
            attachments=[],
            proposal_title=proposal.title,
            prompt_mode="phed",
            user_name=user.name or user.email.split("@")[0].title(),
            user_role=user.role,
            organization_name=user.organization_name,
            user_department=assigned_department or user.department,
            department_description=assigned_department_description  # For revision context
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating proposal: {str(e)}")

    # Update proposal content in database (complete replacement)
    # For revisions, update proposal_revision instead of content
    if proposal.assigned_to_email:
        proposal.proposal_revision = new_content
    else:
        proposal.content = new_content
    proposal.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(proposal)

    return proposal.to_dict()



@app.post("/proposals/{proposal_id}/submit_draft")
async def submit_draft(
    proposal_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Submit a draft proposal for processing and notify relevant sub-departments.
    
    This endpoint:
    1. Gets all users in the same organization (role != owner)
    2. Uses Gemini to identify relevant sub-departments from the draft
    3. Generates personalized proposals for each relevant department
    4. Sends email notifications via Resend to relevant people
    5. Updates the proposal status and final_draft flag
    """
    import traceback
    print(f"\n{'='*60}")
    print(f"[SUBMIT_DRAFT] Starting submit_draft for proposal_id: {proposal_id}")
    print(f"[SUBMIT_DRAFT] User: {user.email}, Org NIF: {user.organization_nif}")
    
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        print(f"[SUBMIT_DRAFT] ERROR: Proposal not found")
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    print(f"[SUBMIT_DRAFT] Found proposal: {proposal.title}")
    print(f"[SUBMIT_DRAFT] Content length: {len(proposal.content or '')}")
    
    if not proposal_revision_service:
        print(f"[SUBMIT_DRAFT] ERROR: Proposal revision service not configured")
        raise HTTPException(status_code=503, detail="Proposal revision service not configured")
    
    try:
        # Step 1: Get all users in same organization (role != owner)
        print(f"[SUBMIT_DRAFT] Step 1: Querying org users with NIF: {user.organization_nif}")
        org_users = db.query(User).filter(
            User.organization_nif == user.organization_nif,
            User.role != 'owner'
        ).all()
        print(f"[SUBMIT_DRAFT] Found {len(org_users)} org users (non-owner)")
        
        # Build list of available departments with full info
        available_departments = [
            {
                "name": u.name or u.email.split("@")[0].title(),
                "department": u.department,
                "email": u.email,
                "department_description": u.department_description or ""
            }
            for u in org_users if u.department
        ]
        print(f"[SUBMIT_DRAFT] Available departments: {len(available_departments)}")
        for dept in available_departments:
            print(f"  - {dept['department']}: {dept['name']} ({dept['email']})")
        
        # Step 2: Extract relevant departments via Gemini
        print(f"[SUBMIT_DRAFT] Step 2: Extracting relevant departments via Gemini")
        relevant_people = []
        if available_departments:
            try:
                relevant_people = await proposal_revision_service.extract_relevant_departments(
                    draft_content=proposal.content or "",
                    available_departments=available_departments
                )
                print(f"[SUBMIT_DRAFT] Extracted {len(relevant_people)} relevant people")
            except Exception as e:
                print(f"[SUBMIT_DRAFT] ERROR in extract_relevant_departments: {e}")
                print(f"[SUBMIT_DRAFT] Traceback: {traceback.format_exc()}")
                raise
        else:
            print(f"[SUBMIT_DRAFT] No available departments, skipping extraction")
        
        # Step 3: For each relevant person, generate personalized proposal and send email
        print(f"[SUBMIT_DRAFT] Step 3: Generating personalized proposals and sending emails")
        email_results = []
        department_proposals = []  # Store for final tender generation
        
        if relevant_people and email_service:
            for i, person in enumerate(relevant_people):
                print(f"[SUBMIT_DRAFT] Processing person {i+1}/{len(relevant_people)}: {person.get('name', 'Unknown')}")
                try:
                    # Generate personalized proposal for this department
                    personalized_proposal = await proposal_revision_service.generate_personalized_proposal(
                        draft_content=proposal.content or "",
                        department_name=person.get("department", ""),
                        department_description=person.get("department_description", ""),
                        recipient_name=person.get("name", "")
                    )
                    print(f"[SUBMIT_DRAFT] Generated personalized proposal for {person.get('name', 'Unknown')}")
                    
                    # Create a new proposal entry for this user with assigned_to_email set
                    # This makes the revision only visible to the assigned user
                    assigned_email = person.get("email", "")
                    
                    # Check if a revision already exists for this user on this proposal
                    existing_revision = db.query(Proposal).filter(
                        Proposal.title == f"{proposal.title} - {person.get('department', 'Revision')}",
                        Proposal.assigned_to_email == assigned_email
                    ).first()
                    
                    if existing_revision:
                        existing_revision.proposal_revision = personalized_proposal
                        existing_revision.updated_at = datetime.utcnow()
                    else:
                        user_revision_proposal = Proposal(
                            user_id=proposal.user_id,  # Original owner
                            title=f"{proposal.title} - {person.get('department', 'Revision')}",
                            content=proposal.content,  # Original content
                            proposal_revision=personalized_proposal,  # Personalized version
                            assigned_to_email=assigned_email,  # Only this user can see it
                            status="revision",
                            final_draft=True
                        )
                        db.add(user_revision_proposal)
                    db.commit()
                    print(f"[SUBMIT_DRAFT] Saved personalized proposal for user {assigned_email}")
                    
                    # Store for final tender generation
                    department_proposals.append({
                        "department": person.get("department", ""),
                        "name": person.get("name", ""),
                        "proposal_content": personalized_proposal
                    })
                    
                    # Send email notification
                    email_result = email_service.send_proposal_notification(
                        to_email=person.get("email", ""),
                        recipient_name=person.get("name", ""),
                        department=person.get("department", ""),
                        proposal_title=proposal.title,
                        proposal_content=personalized_proposal,
                        submitted_by=user.name or user.email.split("@")[0].title()
                    )
                    print(f"[SUBMIT_DRAFT] Email result: {email_result}")
                    email_results.append(email_result)
                except Exception as e:
                    print(f"[SUBMIT_DRAFT] ERROR processing person {person.get('name', 'Unknown')}: {e}")
                    print(f"[SUBMIT_DRAFT] Traceback: {traceback.format_exc()}")
                    raise
        else:
            print(f"[SUBMIT_DRAFT] No relevant people or no email service, skipping email step")
        
        # Step 4: Generate final formal tender document
        print(f"[SUBMIT_DRAFT] Step 4: Generating final tender document")
        final_tender = ""
        if department_proposals:
            try:
                final_tender = await proposal_revision_service.generate_final_tender(
                    draft_content=proposal.content or "",
                    organization_name=user.organization_name or "Government Organization",
                    department_name=user.department or "Department",
                    tender_authority=user.name or "Executive Engineer",
                    department_proposals=department_proposals
                )
                print(f"[SUBMIT_DRAFT] Generated final tender (length: {len(final_tender)})")
            except Exception as e:
                print(f"[SUBMIT_DRAFT] ERROR in generate_final_tender: {e}")
                print(f"[SUBMIT_DRAFT] Traceback: {traceback.format_exc()}")
                raise
        else:
            print(f"[SUBMIT_DRAFT] No department proposals, skipping tender generation")
        
        # Step 5: Update proposal with final tender and status
        print(f"[SUBMIT_DRAFT] Step 5: Updating proposal in database")
        try:
            proposal.status = "submitted"
            proposal.proposal_revision = final_tender  # Store final tender
            proposal.final_draft = True  # Mark as finalized
            proposal.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(proposal)
            print(f"[SUBMIT_DRAFT] Proposal updated successfully")
        except Exception as e:
            print(f"[SUBMIT_DRAFT] ERROR updating proposal in database: {e}")
            print(f"[SUBMIT_DRAFT] Traceback: {traceback.format_exc()}")
            raise
        
        # Step 5.5: Update all assigned revision proposals with the final tender
        if final_tender and relevant_people:
            print(f"[SUBMIT_DRAFT] Step 5.5: Updating assigned revisions with final tender")
            try:
                for person in relevant_people:
                    assigned_email = person.get("email", "")
                    revision_proposal = db.query(Proposal).filter(
                        Proposal.title == f"{proposal.title} - {person.get('department', 'Revision')}",
                        Proposal.assigned_to_email == assigned_email
                    ).first()
                    
                    if revision_proposal:
                        revision_proposal.proposal_revision = final_tender  # Update with final tender
                        revision_proposal.updated_at = datetime.utcnow()
                        print(f"[SUBMIT_DRAFT] Updated revision for {assigned_email} with final tender")
                
                db.commit()
                print(f"[SUBMIT_DRAFT] All assigned revisions updated with final tender")
            except Exception as e:
                print(f"[SUBMIT_DRAFT] ERROR updating assigned revisions: {e}")
                print(f"[SUBMIT_DRAFT] Traceback: {traceback.format_exc()}")
        
        # Count successful emails
        sent_count = sum(1 for r in email_results if r.get("success"))
        failed_count = sum(1 for r in email_results if not r.get("success"))
        
        print(f"[SUBMIT_DRAFT] SUCCESS! Emails sent: {sent_count}, failed: {failed_count}")
        print(f"{'='*60}\n")
        
        return {
            "message": "Draft submitted, notifications sent, and tender generated",
            "id": proposal_id,
            "proposal": proposal.to_dict(),
            "notifications": {
                "relevant_departments": len(relevant_people),
                "emails_sent": sent_count,
                "emails_failed": failed_count
            },
            "tender_generated": bool(final_tender)
        }
    
    except Exception as e:
        print(f"[SUBMIT_DRAFT] FATAL ERROR: {e}")
        print(f"[SUBMIT_DRAFT] Traceback: {traceback.format_exc()}")
        print(f"{'='*60}\n")
        raise HTTPException(status_code=500, detail=f"Error processing draft: {str(e)}")


@app.patch("/proposals/{proposal_id}")
async def rename_proposal(proposal_id: str, data: ProposalRename, db: Session = Depends(get_db)):
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    proposal.title = data.title
    proposal.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(proposal)
    return proposal.to_dict()


@app.delete("/proposals/{proposal_id}")
async def delete_proposal(proposal_id: str, db: Session = Depends(get_db)):
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    db.delete(proposal)
    db.commit()
    return {"message": "Proposal deleted successfully", "id": proposal_id}


@app.post("/proposals/{proposal_id}/pin")
async def pin_proposal(proposal_id: str, db: Session = Depends(get_db)):
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    proposal.pinned = not proposal.pinned
    proposal.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(proposal)
    return proposal.to_dict()


# --- Organizations (from user data) ---
@app.get("/organizations/{org_id}")
async def get_organization(org_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # Count members in same organization
    members_count = db.query(User).filter(User.organization_name == user.organization_name).count()
    return {
        "id": org_id,
        "name": user.organization_name or "Organization",
        "nif": user.organization_nif or "-",
        "members_count": members_count
    }


@app.get("/organizations/{org_id}/members")
async def list_members(org_id: str, role: Optional[str] = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """List all members in the current user's organization."""
    query = db.query(User).filter(User.organization_name == user.organization_name)
    
    if role and role.lower() != "all":
        query = query.filter(User.role == role.lower())
    
    members = query.all()
    return [m.to_dict() for m in members]


@app.get("/organizations/{org_id}/available-users")
async def list_available_users(org_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """List all users that can be added to the organization (not yet in org)."""
    # Get users not in any organization or in a different organization
    users = db.query(User).filter(
        (User.organization_name == None) | (User.organization_name == "")
    ).all()
    return [{"id": str(u.id), "name": u.name or u.email, "email": u.email} for u in users]


class MemberAddByUserId(BaseModel):
    user_id: str
    role: str


@app.post("/organizations/{org_id}/members")
async def add_member(org_id: str, data: MemberAddByUserId, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Add a user to the organization with a specific role."""
    # Check if current user is owner or admin
    if user.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only owners and admins can add members")
    
    # Find the user to add
    target_user = db.query(User).filter(User.id == data.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Add user to organization
    target_user.organization_name = user.organization_name
    target_user.organization_nif = user.organization_nif
    target_user.role = data.role
    db.commit()
    db.refresh(target_user)
    
    return target_user.to_dict()


@app.patch("/organizations/{org_id}/members/{member_id}")
async def update_member_role(org_id: str, member_id: str, data: MemberAdd, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Update a member's role."""
    if user.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only owners and admins can update roles")
    
    target_user = db.query(User).filter(User.id == member_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Member not found")
    
    target_user.role = data.role
    db.commit()
    db.refresh(target_user)
    
    return target_user.to_dict()


@app.delete("/organizations/{org_id}/members/{member_id}")
async def remove_member(org_id: str, member_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Remove a member from the organization."""
    if user.role not in ["owner", "admin"]:
        raise HTTPException(status_code=403, detail="Only owners and admins can remove members")
    
    target_user = db.query(User).filter(User.id == member_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Remove from organization (clear org info)
    target_user.organization_name = None
    target_user.organization_nif = None
    target_user.role = "viewer"
    db.commit()
    
    return {"message": "Member removed successfully"}


# --- Chat with Files ---
@app.post("/proposals/{proposal_id}/chat")
async def chat_with_files(
    proposal_id: str,
    message: str = Form(...),
    files: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Process user input with optional file attachments and update the proposal.
    
    Each call completely replaces the proposal content with the AI-generated
    Draft Proposal. No chat history is maintained.
    """
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    if not gemini_service:
        raise HTTPException(status_code=503, detail="AI service not configured")

    # Process file attachments
    attachments = []
    for file in files:
        try:
            content = await file.read()
            content_type = file.content_type or "application/octet-stream"

            if not FileProcessor.validate_file_type(content_type):
                raise HTTPException(status_code=400, detail=f"Unsupported file type: {content_type}")

            base64_content, extracted_text = FileProcessor.process_file(
                filename=file.filename,
                content=content,
                content_type=content_type
            )

            attachment = FileAttachment(
                id=str(uuid.uuid4())[:8],
                filename=file.filename,
                content_type=content_type,
                size=len(content),
                content=base64_content,
                extracted_text=extracted_text
            )
            attachments.append(attachment)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

    try:
        # For assigned revisions, get department context from the assigned user
        assigned_department = None
        assigned_department_description = None
        
        if proposal.assigned_to_email:
            # This is a revision - look up the assigned user's department info
            assigned_user = db.query(User).filter(User.email == proposal.assigned_to_email).first()
            if assigned_user:
                assigned_department = assigned_user.department
                assigned_department_description = assigned_user.department_description
        
        # Generate updated proposal - this REPLACES the entire content
        # For revisions, use the proposal_revision content instead of content
        current_content = proposal.proposal_revision if proposal.assigned_to_email and proposal.proposal_revision else proposal.content
        
        # Pass user info from Supabase for the "Prepared By" field
        new_content = gemini_service.generate_proposal_response(
            user_message=message,
            current_content=current_content or "",
            attachments=attachments,
            proposal_title=proposal.title,
            prompt_mode="phed",
            user_name=user.name or user.email.split("@")[0].title(),
            user_role=user.role,
            organization_name=user.organization_name,
            user_department=assigned_department or user.department,
            department_description=assigned_department_description  # For revision context
        )

        # Update proposal content in database (complete replacement)
        # For revisions, update proposal_revision instead of content
        if proposal.assigned_to_email:
            proposal.proposal_revision = new_content
        else:
            proposal.content = new_content
        proposal.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(proposal)

        return {
            "proposal": proposal.to_dict(),
            "files_processed": len(attachments)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")



@app.get("/proposals/{proposal_id}/messages")
async def get_chat_history(proposal_id: str, db: Session = Depends(get_db)):
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    history = chat_history_db.get(proposal_id, [])
    return {"messages": history}


@app.get("/my-revisions")
async def get_my_revisions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get all proposal revisions assigned to the current user (by email)."""
    revisions = db.query(Proposal).filter(
        Proposal.assigned_to_email == user.email
    ).all()
    
    return [revision.to_dict() for revision in revisions]


@app.get("/proposals/{proposal_id}/my-revision")
async def get_my_proposal_revision(
    proposal_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Get the personalized proposal revision for the current user."""
    revision = db.query(Proposal).filter(
        Proposal.id == proposal_id,
        Proposal.assigned_to_email == user.email
    ).first()
    
    if not revision:
        raise HTTPException(status_code=404, detail="No revision found for this user on this proposal")
    
    return revision.to_dict()


# --- Active Tenders ---
@app.post("/proposals/{proposal_id}/publish_tender")
async def publish_tender(
    proposal_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Publish a tender from a proposal revision.
    
    This endpoint:
    1. Gets the proposal_revision content (final tender document)
    2. Uses LLM to extract title and price from the tender
    3. Creates an ActiveTender record with auto-calculated dates
    """
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    # Get the tender content (proposal_revision for assigned revisions, otherwise content)
    tender_content = proposal.proposal_revision if proposal.proposal_revision else proposal.content
    
    if not tender_content:
        raise HTTPException(status_code=400, detail="No tender content available to publish")
    
    # Check if tender already exists for this proposal
    existing_tender = db.query(ActiveTender).filter(ActiveTender.proposal_id == proposal.id).first()
    if existing_tender:
        raise HTTPException(status_code=400, detail="Tender already published for this proposal")
    
    # Get organization NIF from user
    organization_nif = user.organization_nif or ""
    if not organization_nif:
        raise HTTPException(status_code=400, detail="User organization NIF is required to publish tender")
    
    # Extract title and price using LLM
    extracted_fields = {"title": proposal.title, "price": 0}
    if active_tender_service:
        try:
            extracted_fields = active_tender_service.extract_tender_fields(tender_content)
        except Exception as e:
            print(f"Warning: LLM extraction failed, using fallback: {e}")
            extracted_fields = {"title": proposal.title, "price": 0}
    
    # Calculate dates
    dates = ActiveTender.calculate_dates()
    
    # Create ActiveTender record
    active_tender = ActiveTender(
        proposal_id=proposal.id,
        title=extracted_fields.get("title", proposal.title),
        organization_nif=organization_nif,
        price=extracted_fields.get("price", 0),
        submission_date=dates["submission_date"],
        submission_deadline=dates["submission_deadline"],
        contract_expiry_date=dates["contract_expiry_date"],
        tender_content=tender_content,
        created_by=user.id
    )
    
    db.add(active_tender)
    db.commit()
    db.refresh(active_tender)
    
    # Update proposal status to 'published'
    proposal.status = "published"
    proposal.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(proposal)
    
    return {
        "message": "Tender published successfully",
        "tender": active_tender.to_dict(),
        "proposal": proposal.to_dict()
    }


@app.get("/active-tenders")
async def list_active_tenders(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    List all active tenders for the user's organization.
    Returns tenders where organization_nif matches the current user's organization.
    """
    if not user.organization_nif:
        return []
    
    tenders = db.query(ActiveTender).filter(
        ActiveTender.organization_nif == user.organization_nif
    ).order_by(ActiveTender.submission_date.desc()).all()
    
    return [tender.to_dict() for tender in tenders]


@app.get("/active-tenders/{tender_id}")
async def get_active_tender(
    tender_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Get a single active tender by ID.
    """
    tender = db.query(ActiveTender).filter(ActiveTender.id == tender_id).first()
    if not tender:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    # Optional: verify user has access to this tender
    # if tender.organization_nif != user.organization_nif:
    #     raise HTTPException(status_code=403, detail="Access denied")
    
    return tender.to_dict()


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "gemini_service": "configured" if gemini_service else "not_configured",
        "active_tender_service": "configured" if active_tender_service else "not_configured",
        "database": "connected"
    }


@app.get("/")
async def root():
    return {
        "message": "Uniflow backend is running",
        "docs": "/docs",
        "health": "/health"
    }
