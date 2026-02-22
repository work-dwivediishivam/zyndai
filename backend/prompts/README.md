# Problem Drafting Prompts

This directory contains specialized system prompts for the Uniflow problem drafting assistant.

## Workflow Overview

```
┌─────────────────┐     ┌────────────────────┐     ┌────────────────────┐
│  Administrator  │────▶│  Problem Draft     │────▶│  Department Heads  │
│  (PHED Admin)   │     │  Document          │     │  (Review & Decide) │
└─────────────────┘     └────────────────────┘     └────────────────────┘
         │                       │                         │
         ▼                       ▼                         ▼
   Problem Description     AI-Generated           Feasibility Assessment
   / Constraints           Markdown Doc           → Proposal Decision
```

## Key Behavior

- **Direct Content Replacement**: Each user input generates a complete Problem Draft that **replaces** the current content entirely
- **No Chat History**: Messages are not accumulated; the AI always sees only the current document and the new instruction
- **Iterative Refinement**: Users can continuously refine the problem articulation
- **Markdown Output**: All documents are generated in clean, structured Markdown format
- **Dynamic User Info**: The "Prepared By" field is populated from Supabase user data
- **Current Date/Time**: The document date is automatically set to the current timestamp

## Available Prompts

### 1. PHED Rajasthan (`phed_rajasthan.py`)

**Target:** Public Health Engineering Department (PHED), Government of Rajasthan

**Purpose:** Articulate organizational/operational problems for departmental review

**Schema (8 Sections):**
1. Problem Overview
2. Background & Operating Context
3. Current State & Observed Gaps
4. Impact Assessment
5. Constraints & Limitations (Budget, HR, Time, Other)
6. What Is Needed to Address the Problem
7. Risks & Considerations
8. Priority & Decision Sensitivity

**Default Assumptions (when not specified by user):**
- Budget impact = 0
- Additional manpower required = 0
- No explicit timeline constraint

## Usage

### Python API

```python
from prompts.phed_rajasthan import get_formatted_prompt

# Get formatted prompt with user info and current date
prompt = get_formatted_prompt(
    user_name="Rajesh Kumar",
    user_role="admin"
)
# Returns prompt with "Prepared By: Rajesh Kumar, Admin" and current date/time
```

### REST API Endpoints

```bash
# Create a new proposal (document container)
POST /proposals
{
  "title": "Water Scarcity in Barmer District"
}

# Iterate on the problem document (content is REPLACED)
POST /proposals/{proposal_id}/iterate
Authorization: Bearer <token>
{
  "user_input": "We are facing acute water shortage in 15 villages of Barmer block. The existing hand pumps are running dry due to falling groundwater levels. This is affecting 12,000 households."
}

# Iterate with files (content is REPLACED)
POST /proposals/{proposal_id}/chat
Authorization: Bearer <token>
# multipart/form-data with:
# - message: "Update based on the attached field report"
# - files: [field_report.pdf]
```

### Response Behavior

Each API call returns the updated document with completely regenerated content:

```json
{
  "id": "abc123",
  "title": "Water Scarcity in Barmer District",
  "content": "# Problem Draft Document\n\n**Department:** Public Health Engineering...",
  "status": "draft",
  "updated_at": "2025-12-13T21:17:00Z"
}
```

## Files

| File | Description |
|------|-------------|
| `__init__.py` | Module exports |
| `phed_rajasthan.py` | PHED Rajasthan problem drafting prompt |
| `README.md` | This documentation |
