"""
Active Tender Service - extracts tender fields using LLM.

This service is used when a user clicks "Publish Tender" to extract
required fields from the proposal revision content.
"""
import os
import json
from openai import OpenAI
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend directory (parent of services/)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)


# Prompt for extracting tender fields
EXTRACT_TENDER_FIELDS_PROMPT = """
# Tender Field Extractor

You are extracting key fields from a tender document to store in a database.

## Tender Document:

```markdown
{tender_content}
```

## Required Fields to Extract:

1. **title**: The main title of the tender (usually the first heading or a clear descriptive title)
2. **price**: The estimated tender value or total price as an INTEGER (in the local currency, no decimals). If no price is mentioned, return 0.

## Output Instructions:

Return ONLY a valid JSON object with the extracted fields. Do not include any explanation or additional text.

Output format:
```json
{{
  "title": "Extracted tender title here",
  "price": 0
}}
```

Important:
- The title should be concise but descriptive (max 500 characters)
- The price must be an integer (no decimals, no currency symbols)
- If you cannot find a price, use 0
- Do not include markdown code fences in your response, just the raw JSON
""".strip()


class ActiveTenderService:
    """Service for extracting tender fields using OpenAI."""
    
    MODEL_NAME = "gpt-4o-mini"
    
    def __init__(self, api_key: str = None):
        """
        Initialize the Active Tender Service.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=self.api_key)
    
    def extract_tender_fields(self, tender_content: str) -> Dict[str, Any]:
        """
        Extract required fields from tender content using LLM.
        
        Args:
            tender_content: The markdown content of the tender document
            
        Returns:
            Dict with extracted fields: {title, price}
        """
        prompt = EXTRACT_TENDER_FIELDS_PROMPT.format(tender_content=tender_content)
        
        try:
            response = self.client.chat.completions.create(
                model=self.MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            response_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            extracted = json.loads(response_text)
            
            # Validate and clean the extracted data
            title = extracted.get("title", "Untitled Tender")[:500]  # Max 500 chars
            
            # Ensure price is an integer
            price = extracted.get("price", 0)
            if isinstance(price, str):
                # Remove any non-numeric characters and convert
                price = ''.join(filter(str.isdigit, price))
                price = int(price) if price else 0
            elif isinstance(price, float):
                price = int(price)
            elif not isinstance(price, int):
                price = 0
            
            return {
                "title": title,
                "price": price
            }
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            # Fallback: try to extract title from first line
            first_line = tender_content.split('\n')[0].strip()
            if first_line.startswith('#'):
                title = first_line.lstrip('#').strip()[:500]
            else:
                title = "Untitled Tender"
            return {"title": title, "price": 0}
            
        except Exception as e:
            error_msg = str(e)
            if "quota" in error_msg.lower() or "rate" in error_msg.lower():
                raise Exception("API quota/rate limit exceeded. Please check your OpenAI API quota.")
            elif "api key" in error_msg.lower() or "authentication" in error_msg.lower():
                raise Exception("Invalid API key. Please check your OPENAI_API_KEY.")
            else:
                raise Exception(f"Error extracting tender fields: {error_msg}")
