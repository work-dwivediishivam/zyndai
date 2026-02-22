"""
Proposal Revision Service - handles processing of submitted drafts.

This service is separate from the main Gemini service and is specifically
for processing drafts when the user clicks "Submit Draft".

Three-step process:
1. Extract relevant sub-departments from the draft
2. Generate personalized proposals for each relevant department
3. Generate final formal tender document consolidating all inputs
"""
import os
import json
from openai import OpenAI
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
from prompts.submit_draft import (
    get_submit_draft_prompt,
    get_extract_departments_prompt,
    get_personalized_proposal_prompt,
    get_final_tender_prompt,
    summarize_department_proposals
)

# Load .env from backend directory (parent of services/)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


class ProposalRevisionService:
    """Service for processing submitted draft proposals using OpenAI."""
    
    MODEL_NAME = "gpt-4o-mini"
    
    def __init__(self, api_key: str = None):
        """
        Initialize the Proposal Revision Service.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def _strip_markdown_fences(self, content: str) -> str:
        """Strip markdown code fences from content if present.
        
        OpenAI sometimes wraps responses in ```markdown ... ``` blocks.
        This function removes those fences to get clean markdown.
        """
        if not content:
            return content
        
        content = content.strip()
        
        # Check for ```markdown or ```md or just ``` at the start
        if content.startswith("```markdown"):
            content = content[len("```markdown"):].strip()
        elif content.startswith("```md"):
            content = content[len("```md"):].strip()
        elif content.startswith("```"):
            content = content[3:].strip()
        
        # Remove trailing ```
        if content.endswith("```"):
            content = content[:-3].strip()
        
        return content
    
    async def extract_relevant_departments(
        self,
        draft_content: str,
        available_departments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Step 1: Extract relevant departments from the draft.
        
        Uses OpenAI to analyze the draft content and identify which
        departments from the available list are most relevant.
        
        Args:
            draft_content: The markdown content of the draft document
            available_departments: List of dicts with {name, department, email, department_description}
            
        Returns:
            List of relevant department dicts from the input list
        """
        # Convert departments to JSON for the prompt
        departments_json = json.dumps(available_departments, indent=2)
        
        # Build the prompt
        prompt = get_extract_departments_prompt(
            draft_content=draft_content,
            departments_json=departments_json
        )
        
        try:
            # Generate response using OpenAI
            response = self.client.chat.completions.create(
                model=self.MODEL_NAME,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            # Parse JSON response
            relevant_departments = json.loads(response_text)
            
            if not isinstance(relevant_departments, list):
                return []
            
            return relevant_departments
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Raw response: {response_text}")
            return []
        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "rate" in error_msg.lower():
                raise Exception("API quota/rate limit exceeded. Please check your OpenAI API quota.")
            elif "api key" in error_msg.lower() or "authentication" in error_msg.lower():
                raise Exception("Invalid API key. Please check your OPENAI_API_KEY.")
            else:
                raise Exception(f"Error extracting departments: {error_msg}")
    
    async def generate_personalized_proposal(
        self,
        draft_content: str,
        department_name: str,
        department_description: str,
        recipient_name: str
    ) -> str:
        """
        Step 2: Generate a personalized proposal for a specific department.
        
        Takes the original draft and creates a tailored version that
        addresses the problem from the target department's perspective.
        
        Args:
            draft_content: The markdown content of the draft document
            department_name: Name of the target department
            department_description: Description of the department's responsibilities
            recipient_name: Name of the recipient
            
        Returns:
            Personalized proposal content in Markdown format
        """
        # Build the prompt
        prompt = get_personalized_proposal_prompt(
            draft_content=draft_content,
            department_name=department_name,
            department_description=department_description,
            recipient_name=recipient_name
        )
        
        try:
            # Generate response using OpenAI
            response = self.client.chat.completions.create(
                model=self.MODEL_NAME,
                messages=[{"role": "user", "content": prompt}]
            )
            return self._strip_markdown_fences(response.choices[0].message.content)
            
        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "rate" in error_msg.lower():
                raise Exception("API quota/rate limit exceeded. Please check your OpenAI API quota.")
            elif "api key" in error_msg.lower() or "authentication" in error_msg.lower():
                raise Exception("Invalid API key. Please check your OPENAI_API_KEY.")
            else:
                raise Exception(f"Error generating personalized proposal: {error_msg}")
    
    async def process_submitted_draft(self, draft_content: str) -> str:
        """
        Legacy method: Process a submitted draft document using OpenAI.
        
        This method is called when a user clicks "Submit Draft". It takes
        the markdown content of the draft and processes it according to
        the submit_draft prompt.
        
        Args:
            draft_content: The markdown content of the draft document
            
        Returns:
            Processed output from OpenAI
        """
        # Get the system prompt for processing submitted drafts
        system_prompt = get_submit_draft_prompt()
        
        # Build the full prompt
        full_prompt = f"""{system_prompt}

---

## Draft Document to Process

```markdown
{draft_content}
```

---

**Process the above draft document according to the instructions.**
"""
        
        try:
            # Generate response using OpenAI
            response = self.client.chat.completions.create(
                model=self.MODEL_NAME,
                messages=[{"role": "user", "content": full_prompt}]
            )
            return self._strip_markdown_fences(response.choices[0].message.content)
        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "rate" in error_msg.lower():
                raise Exception("API quota/rate limit exceeded. Please check your OpenAI API quota.")
            elif "api key" in error_msg.lower() or "authentication" in error_msg.lower():
                raise Exception("Invalid API key. Please check your OPENAI_API_KEY.")
            else:
                raise Exception(f"Error processing submitted draft: {error_msg}")
    
    async def generate_final_tender(
        self,
        draft_content: str,
        organization_name: str,
        department_name: str,
        tender_authority: str,
        department_proposals: List[Dict[str, Any]]
    ) -> str:
        """
        Step 3: Generate the final formal tender document.
        
        Consolidates all department proposals into a unified, publication-ready
        tender document following government guidelines.
        
        Args:
            draft_content: The original markdown content of the draft document
            organization_name: Name of the organization
            department_name: Name of the primary department
            tender_authority: Name/designation of the tender inviting authority
            department_proposals: List of dicts with {department, name, proposal_content}
            
        Returns:
            Complete formal tender document in Markdown format
        """
        # Get current date for publish date
        publish_date = datetime.now().strftime("%d-%b-%Y %I:%M %p")
        
        # Summarize department proposals (handles context size)
        proposals_summary = summarize_department_proposals(department_proposals)
        
        # Build the prompt
        prompt = get_final_tender_prompt(
            organization_name=organization_name,
            department_name=department_name,
            tender_authority=tender_authority,
            draft_content=draft_content,
            department_proposals=proposals_summary,
            publish_date=publish_date
        )
        
        try:
            # Generate response using OpenAI
            response = self.client.chat.completions.create(
                model=self.MODEL_NAME,
                messages=[{"role": "user", "content": prompt}]
            )
            return self._strip_markdown_fences(response.choices[0].message.content)
            
        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "rate" in error_msg.lower():
                raise Exception("API quota/rate limit exceeded. Please check your OpenAI API quota.")
            elif "api key" in error_msg.lower() or "authentication" in error_msg.lower():
                raise Exception("Invalid API key. Please check your OPENAI_API_KEY.")
            else:
                raise Exception(f"Error generating final tender: {error_msg}")

