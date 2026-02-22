"""
Email service using Resend for sending proposal notifications.
"""
import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend directory (parent of services/)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False
    print("⚠ Warning: resend package not installed. Run: pip install resend")


class EmailService:
    """Service for sending emails via Resend."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Email Service.
        
        Args:
            api_key: Resend API key (defaults to RESEND_API_KEY env var)
        """
        if not RESEND_AVAILABLE:
            raise ImportError("resend package is not installed. Run: pip install resend")
        
        self.api_key = api_key or os.getenv("RESEND_API_KEY")
        if not self.api_key:
            raise ValueError("RESEND_API_KEY environment variable not set")
        
        resend.api_key = self.api_key
    
    def send_proposal_notification(
        self,
        to_email: str,
        recipient_name: str,
        department: str,
        proposal_title: str,
        proposal_content: str,
        submitted_by: str
    ) -> dict:
        """
        Send a personalized proposal draft notification email.
        
        Args:
            to_email: Recipient email address
            recipient_name: Name of the recipient
            department: Recipient's department
            proposal_title: Title of the proposal
            proposal_content: Personalized proposal content (markdown/html)
            submitted_by: Name of the person who submitted the draft
            
        Returns:
            Resend API response with email ID
        """
        # Simplified email - no content, just login link
        app_url = os.getenv("FRONTEND_URL", "https://uniflow-pqmm.vercel.app")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px 8px 0 0; text-align: center; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .content {{ background: #f9fafb; padding: 40px 30px; border: 1px solid #e5e7eb; text-align: center; }}
                .btn {{ display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 16px 40px; text-decoration: none; border-radius: 8px; margin-top: 25px; font-weight: 600; font-size: 16px; }}
                .btn:hover {{ opacity: 0.9; }}
                .footer {{ padding: 20px; text-align: center; color: #6b7280; font-size: 14px; border-radius: 0 0 8px 8px; background: #f3f4f6; }}
                .proposal-title {{ color: #667eea; font-size: 20px; margin: 20px 0 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📋 New Proposal Request</h1>
                </div>
                <div class="content">
                    <p>Dear <strong>{recipient_name}</strong>,</p>
                    <p><strong>{submitted_by}</strong> has requested your department (<strong>{department}</strong>) to review and contribute to a proposal.</p>
                    
                    <p class="proposal-title">"{proposal_title}"</p>
                    
                    <p style="color: #6b7280; margin-top: 20px;">Log in to UniFlow to view the full proposal and provide your input.</p>
                    
                    <a href="{app_url}" class="btn">View Proposal in UniFlow →</a>
                </div>
                <div class="footer">
                    <p>This is an automated notification from UniFlow.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            response = resend.Emails.send({
                "from": "onboarding@resend.dev",  # Resend sandbox domain
                "to": to_email,
                "subject": f"Proposal Request: {proposal_title}",
                "html": html_content
            })
            return {"success": True, "id": response.get("id"), "email": to_email}
        except Exception as e:
            # Fallback: try sending to fallback email instead
            fallback_email = os.getenv("FALLBACK_EMAIL", "sde.tusharchandra@gmail.com")
            print(f"[EMAIL] Failed to send to {to_email}: {e}")
            print(f"[EMAIL] Retrying with fallback email: {fallback_email}")
            
            try:
                # Modify subject to indicate this is a forwarded notification
                fallback_subject = f"[FWD to {recipient_name}] Proposal Request: {proposal_title}"
                
                # Add note about original recipient
                fallback_html = html_content.replace(
                    f"Dear <strong>{recipient_name}</strong>",
                    f"Dear <strong>{recipient_name}</strong><br><em style='color: #6b7280;'>(Original recipient: {to_email} - forwarded due to email restriction)</em>"
                )
                
                response = resend.Emails.send({
                    "from": "onboarding@resend.dev",
                    "to": fallback_email,
                    "subject": fallback_subject,
                    "html": fallback_html
                })
                return {
                    "success": True, 
                    "id": response.get("id"), 
                    "email": fallback_email,
                    "original_email": to_email,
                    "fallback_used": True
                }
            except Exception as fallback_error:
                return {
                    "success": False, 
                    "error": str(fallback_error), 
                    "email": to_email,
                    "fallback_attempted": fallback_email
                }
    
    def send_batch_notifications(
        self,
        recipients: list,
        proposal_title: str,
        submitted_by: str,
        personalized_proposals: dict
    ) -> dict:
        """
        Send notifications to multiple recipients with personalized proposals.
        
        Args:
            recipients: List of dicts with {name, email, department}
            proposal_title: Title of the proposal
            submitted_by: Name of the submitter
            personalized_proposals: Dict mapping department to personalized proposal content
            
        Returns:
            Summary of sent emails with success/failure counts
        """
        results = {
            "sent": [],
            "failed": [],
            "total": len(recipients)
        }
        
        for recipient in recipients:
            dept = recipient.get("department", "")
            proposal_content = personalized_proposals.get(dept, "")
            
            result = self.send_proposal_notification(
                to_email=recipient["email"],
                recipient_name=recipient["name"],
                department=dept,
                proposal_title=proposal_title,
                proposal_content=proposal_content,
                submitted_by=submitted_by
            )
            
            if result.get("success"):
                results["sent"].append(result)
            else:
                results["failed"].append(result)
        
        return results
