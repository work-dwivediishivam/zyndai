"""
AI service for chat and proposal generation.
Uses OpenAI GPT-4o-mini model with context management.
"""
import os
import tiktoken
from openai import OpenAI
from typing import List, Optional, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
from models.chat import ChatMessage, FileAttachment
from prompts.phed_rajasthan import PHED_RAJASTHAN_SYSTEM_PROMPT, get_formatted_prompt
from prompts.submit_draft import get_submit_draft_prompt

# Load .env from backend directory (parent of services/)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


# Default general-purpose proposal writing prompt
GENERAL_PROPOSAL_PROMPT = """You are an expert proposal writer assistant. Your role is to help users create, iterate, and improve professional proposals.

When responding:
1. Generate well-structured, professional content in Markdown format
2. Use appropriate headings, lists, and formatting
3. Be concise but comprehensive
4. If files are attached, analyze them and incorporate relevant information
5. Maintain context from previous messages in the conversation
6. For images, describe what you see and how it relates to the proposal

Always format your responses in clean Markdown."""


class GeminiService:
    """Service for interacting with OpenAI GPT models"""
    
    # Context window for GPT-4o-mini (conservative estimate)
    MAX_CONTEXT_TOKENS = 120000  # ~128k tokens, leaving buffer
    MODEL_NAME = "gpt-4o-mini"
    
    def __init__(self, api_key: Optional[str] = None, enable_search: bool = True):
        """Initialize AI service
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            enable_search: Not used with OpenAI (kept for compatibility)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=self.api_key)
        self.enable_search = enable_search  # Kept for compatibility
        
        # Initialize tokenizer for counting
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except:
            self.tokenizer = None
    
    def count_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        # Rough estimate: 1 token ≈ 4 characters
        return len(text) // 4
    
    def generate_proposal_response(
        self,
        user_message: str,
        current_content: str = "",
        attachments: List[FileAttachment] = None,
        proposal_title: str = "",
        prompt_mode: str = "phed",
        user_name: str = None,
        user_role: str = None,
        organization_name: str = None,
        user_department: str = None,
        department_description: str = None  # For revision context
    ) -> str:
        """
        Generate or update a draft proposal using Gemini.
        
        This method generates a complete Markdown document that replaces the
        current proposal content. No chat history is maintained - each call
        produces a fresh, complete proposal based on the user's instruction
        and the current content.
        
        Args:
            user_message: The user's instruction (problem statement, update request, etc.)
            current_content: Current proposal Markdown content (empty for new proposals)
            attachments: File attachments to incorporate
            proposal_title: Title of the proposal
            prompt_mode: System prompt mode ("phed" for PHED Rajasthan, "general" for generic)
            user_name: Name of the current user (from Supabase)
            user_role: Role/designation of the current user
            organization_name: Organization name of the user (from Supabase)
            user_department: Department of the user (from Supabase)
            
        Returns:
            Complete Markdown proposal document (replaces current content entirely)
        """
        # Build the prompt
        prompt_parts = []
        
        # Select system prompt based on mode
        if prompt_mode == "phed":
            # Use formatted prompt with user info
            system_prompt = get_formatted_prompt(
                user_name=user_name,
                user_role=user_role,
                organization_name=organization_name,
                user_department=user_department
            )
        else:
            system_prompt = GENERAL_PROPOSAL_PROMPT
        
        prompt_parts.append(system_prompt)

        # Add department context if this is a revision for a specific department
        if department_description:
            prompt_parts.append("\n---\n")
            prompt_parts.append("## Department Context")
            prompt_parts.append(f"You are revising this proposal for the **{user_department or 'Department'}**.")
            prompt_parts.append(f"**Department Description:** {department_description}")
            prompt_parts.append("Consider this department's perspective and responsibilities when making revisions.")
        
        # Add current proposal content if exists (for iteration)
        if current_content and current_content.strip():
            prompt_parts.append("\n---\n")
            prompt_parts.append("## Current Proposal (to be updated)")
            prompt_parts.append("The following is the current draft. Update it based on the user's instruction below.")
            prompt_parts.append("\n```markdown")
            # Truncate if too long
            content_tokens = self.count_tokens(current_content)
            if content_tokens > 50000:
                current_content = current_content[:200000] + "\n\n[... content truncated ...]"
            prompt_parts.append(current_content)
            prompt_parts.append("```\n")
        
        # Add file attachments
        if attachments:
            prompt_parts.append("\n---\n")
            prompt_parts.append("## Reference Documents")
            prompt_parts.append("**IMPORTANT**: The user has provided the following reference documents. You MUST:")
            prompt_parts.append("1. Carefully analyze all attached documents")
            prompt_parts.append("2. Extract relevant data, specifications, requirements, and context")
            prompt_parts.append("3. Incorporate this information into the proposal where appropriate")
            prompt_parts.append("4. Reference specific details from the documents to strengthen the proposal")
            prompt_parts.append("5. For images, describe what you see and integrate visual information into the proposal\n")
            
            for attachment in attachments:
                if attachment.extracted_text:
                    text = attachment.extracted_text
                    if len(text) > 100000:
                        text = text[:100000] + "\n\n[... file content truncated ...]"
                    prompt_parts.append(f"\n### File: {attachment.filename}")
                    prompt_parts.append(f"Content Type: {attachment.content_type}")
                    prompt_parts.append(f"```\n{text}\n```")
        
        # Add user instruction
        prompt_parts.append("\n---\n")
        prompt_parts.append("## User Instruction")
        prompt_parts.append(user_message)
        
        # Add title context if provided
        if proposal_title:
            prompt_parts.append(f"\n\n(Proposal Title: {proposal_title})")
        
        # Final instruction
        prompt_parts.append("\n---\n")
        prompt_parts.append("**Generate the complete, updated Draft Proposal in Markdown format. Output ONLY the proposal document, no other text.**")
        
        # Combine all parts
        full_prompt = "\n".join(prompt_parts)
        
        # Check total token count and truncate if needed
        total_tokens = self.count_tokens(full_prompt)
        if total_tokens > self.MAX_CONTEXT_TOKENS:
            # Aggressive truncation - prioritize user instruction, system prompt, and attachments
            prompt_parts = [
                system_prompt,
                "\n---\n",
            ]
            
            # Include attachments with truncated content
            if attachments:
                prompt_parts.append("## Reference Documents")
                prompt_parts.append("**IMPORTANT**: Analyze and incorporate information from these documents:\n")
                
                # Include up to 3 attachments with truncated content
                for i, attachment in enumerate(attachments[:3]):
                    if attachment.extracted_text:
                        # Allocate ~30k chars per attachment
                        text = attachment.extracted_text[:30000]
                        if len(attachment.extracted_text) > 30000:
                            text += "\n\n[... content truncated ...]"
                        prompt_parts.append(f"\n### File {i+1}: {attachment.filename}")
                        prompt_parts.append(f"```\n{text}\n```\n")
                
                prompt_parts.append("\n---\n")
            
            # Add user instruction
            prompt_parts.extend([
                "## User Instruction",
                user_message,
                "\n---\n",
                "**Generate the complete Draft Proposal in Markdown format. Output ONLY the proposal document.**"
            ])
            
            full_prompt = "\n".join(prompt_parts)

        

        # Generate response
        try:
            # Handle images separately with vision model
            if attachments and any(att.content_type.startswith('image/') for att in attachments):
                return self._generate_with_vision(full_prompt, attachments)
            
            response = self.client.chat.completions.create(
                model=self.MODEL_NAME,
                messages=[{"role": "user", "content": full_prompt}]
            )
            content = response.choices[0].message.content
            # Strip markdown code fences if present
            return self._strip_markdown_fences(content)
        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "rate" in error_msg.lower():
                raise Exception("API quota/rate limit exceeded. Please check your OpenAI API quota.")
            elif "api key" in error_msg.lower() or "authentication" in error_msg.lower():
                raise Exception("Invalid API key. Please check your OPENAI_API_KEY.")
            else:
                raise Exception(f"Error generating response: {error_msg}")
    
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
    
    def _generate_with_vision(self, prompt: str, attachments: List[FileAttachment]) -> str:
        """Generate response with vision model for images"""
        import base64
        
        # Build content with images for OpenAI vision
        content_parts = [{"type": "text", "text": prompt}]
        
        # Add images to the request
        for attachment in attachments:
            if attachment.content_type.startswith('image/'):
                try:
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{attachment.content_type};base64,{attachment.content}"
                        }
                    })
                except Exception as e:
                    print(f"Error processing image {attachment.filename}: {e}")
        
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL_NAME,
                messages=[{"role": "user", "content": content_parts}]
            )
            content = response.choices[0].message.content
            return self._strip_markdown_fences(content)
        except Exception as e:
            raise Exception(f"Error generating response with vision: {str(e)}")
    
    def summarize_document(self, text: str, filename: str) -> str:
        """Generate a summary of a document"""
        prompt = f"""Please provide a concise summary of the following document: {filename}

Document content:
{text[:50000]}

Provide a summary in 3-5 bullet points highlighting the key information."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL_NAME,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error summarizing document: {str(e)}"
    
    def process_submitted_draft(self, draft_content: str) -> str:
        """
        Process a submitted draft document using OpenAI.
        
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
            response = self.client.chat.completions.create(
                model=self.MODEL_NAME,
                messages=[{"role": "user", "content": full_prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "rate" in error_msg.lower():
                raise Exception("API quota/rate limit exceeded. Please check your OpenAI API quota.")
            elif "api key" in error_msg.lower() or "authentication" in error_msg.lower():
                raise Exception("Invalid API key. Please check your OPENAI_API_KEY.")
            else:
                raise Exception(f"Error processing submitted draft: {error_msg}")
