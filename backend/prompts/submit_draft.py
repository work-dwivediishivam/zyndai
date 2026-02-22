"""
System prompts for processing submitted draft documents.

This module contains prompts used when a user clicks "Submit Draft" to:
1. Extract relevant sub-departments from the draft
2. Generate personalized proposals for each relevant department
"""

# Prompt 1: Extract relevant departments from the draft
EXTRACT_DEPARTMENTS_PROMPT = """
# Department Relevance Analyzer

You are analyzing a problem draft document to identify which sub-departments within an organization should be notified for review.

## Available Sub-Departments in Organization:

The following people and their departments are available in this organization:

```json
{departments_json}
```

## Draft Document:

```markdown
{draft_content}
```

## Your Task:

1. Carefully read and understand the problem described in the draft
2. Analyze which departments would be most relevant to review and contribute to this problem
3. Consider the department descriptions to understand each department's expertise
4. Select ONLY the departments that have direct relevance to the problem

## Output Instructions:

Return ONLY a valid JSON array with the relevant people. Do not include any explanation or additional text.
Include only people whose departments are directly relevant to the problem.

Output format:
```json
[
  {{
    "name": "Person Name",
    "department": "Department Name",
    "email": "email@example.com",
    "department_description": "Description of department responsibilities"
  }}
]
```

If no departments are clearly relevant, return an empty array: []
""".strip()


# Prompt 2: Generate personalized proposal for a specific department
GENERATE_PERSONALIZED_PROPOSAL_PROMPT = """
# Personalized Proposal Generator

You are creating a tailored proposal draft for a specific department based on an original problem document.

## Original Problem Draft:

```markdown
{draft_content}
```

## Target Department Information:

- **Department Name:** {department_name}
- **Department Description:** {department_description}
- **Recipient Name:** {recipient_name}

## Your Task:

Create a personalized proposal draft that:

1. **Addresses the problem from this department's perspective**
   - Highlight aspects most relevant to their expertise
   - Frame the problem in terms they would understand and care about

2. **Suggests specific actions or contributions**
   - What could this department contribute to solving the problem?
   - What expertise or resources might they offer?

3. **Maintains professional tone**
   - Keep it concise but comprehensive
   - Use clear, actionable language

4. **Structures the proposal clearly**
   - Use appropriate headings and sections
   - Make it easy to scan and understand

## Output Instructions:

Output a clean, professional proposal in Markdown format.
The proposal should be no longer than 500-800 words.
Do not include any meta-commentary, only output the proposal content.

---
""".strip()


def get_extract_departments_prompt(draft_content: str, departments_json: str) -> str:
    """
    Get the formatted prompt for extracting relevant departments.
    
    Args:
        draft_content: The markdown content of the draft document
        departments_json: JSON string of available departments with their info
        
    Returns:
        Formatted prompt string
    """
    return EXTRACT_DEPARTMENTS_PROMPT.format(
        draft_content=draft_content,
        departments_json=departments_json
    )


def get_personalized_proposal_prompt(
    draft_content: str,
    department_name: str,
    department_description: str,
    recipient_name: str
) -> str:
    """
    Get the formatted prompt for generating a personalized proposal.
    
    Args:
        draft_content: The markdown content of the draft document
        department_name: Name of the target department
        department_description: Description of the department's responsibilities
        recipient_name: Name of the recipient
        
    Returns:
        Formatted prompt string
    """
    return GENERATE_PERSONALIZED_PROPOSAL_PROMPT.format(
        draft_content=draft_content,
        department_name=department_name,
        department_description=department_description or "No description available",
        recipient_name=recipient_name
    )


# Legacy prompt (kept for backward compatibility)
SUBMIT_DRAFT_SYSTEM_PROMPT = """
# Draft Document Processor

This prompt processes submitted problem draft documents.
The markdown content of the draft will be passed as input.

Processing tasks:
- Validation of the document structure
- Generating a summary for reviewers
- Creating action items
- Preparing the document for departmental review

---
""".strip()


def get_submit_draft_prompt() -> str:
    """
    Get the system prompt for processing submitted drafts.
    
    Returns:
        The system prompt string
    """
    return SUBMIT_DRAFT_SYSTEM_PROMPT


# Prompt 3: Generate final formal tender document
GENERATE_FINAL_TENDER_PROMPT = """
# Official Government Tender Document Generator

You are generating a formal tender document for publication on the eProcurement System, Government of Rajasthan.
This tender must follow strict government guidelines and include all mandatory sections.

---

## Organization Information:

**Organisation:** {organization_name}
**Department:** {department_name}
**Tender Inviting Authority:** {tender_authority}

---

## Original Problem Draft:

```markdown
{draft_content}
```

---

## Department Contributions (Consolidated):

The following departments have provided their input on this proposal:

{department_proposals}

---

## Your Task:

Generate a **formal tender document** that consolidates all department inputs into a unified, publication-ready tender.

### MANDATORY SECTIONS (Must Always Include):

#### 1. Tender Basic Information
```
| Field | Value |
|-------|-------|
| Tender Reference Number | [Auto-generate: ORG/DEPT/YYYY/XXXX format] |
| Tender Title | [Clear, descriptive title from problem draft] |
| Tender Category | [Works/Goods/Services/Consultancy] |
| Tender Type | [Open/Limited/Single] |
| Organisation | {organization_name} |
| Department | {department_name} |
```

#### 2. Critical Dates
```
| Date Type | Date & Time |
|-----------|-------------|
| Publish Date | {publish_date} |
| Document Download Start Date | {publish_date} |
| Document Download End Date | [Publish + 7 days] |
| Clarification Start Date | [Publish + 1 day] |
| Clarification End Date | [Publish + 5 days] |
| Bid Submission Start Date | {publish_date} |
| Bid Submission End Date | [Publish + 7 days, 6:00 PM] |
| Bid Opening Date | [Bid End + 1 day, 1:00 PM] |
| Financial Bid Opening Date | [Bid Opening + 7 days] |
```

#### 3. Tender Value & EMD
```
| Field | Value |
|-------|-------|
| Estimated Tender Value | [Extract from draft or calculate] |
| EMD Amount | [2% of tender value] |
| Tender Fee | [As per government norms] |
| Bid Validity Period | 90 days |
```

#### 4. Tender Inviting Authority
```
| Field | Value |
|-------|-------|
| Name | {tender_authority} |
| Designation | [Appropriate designation] |
| Address | [Department address] |
| Contact | [Department contact] |
```

### DYNAMIC SECTIONS (Generate from Draft & Department Inputs):

#### 5. Scope of Work
- Consolidate problem description from draft
- Integrate specific requirements from all departments
- Define clear deliverables

#### 6. Technical Specifications
- Extract technical requirements from draft
- Include department-specific technical inputs
- List mandatory compliance requirements

#### 7. Eligibility Criteria
- Minimum experience requirements
- Financial capacity requirements
- Technical capability requirements
- Registration/license requirements

#### 8. Bill of Quantities (BOQ) Summary
Generate a summary table of major work items with:
- S.No
- Description
- Unit
- Quantity
- Estimated Rate
- Estimated Amount

#### 9. Budget Allocation by Department
**IMPORTANT FOR COLLABORATIVE PROJECTS:**
If multiple departments are involved, intelligently split the budget:
- Identify each department's contribution scope
- Allocate budget proportionally based on scope
- Ensure total matches estimated tender value
- Show breakdown in table format

#### 10. Terms & Conditions
- Payment terms
- Performance guarantee requirements
- Liquidated damages clause
- Force majeure clause
- Dispute resolution mechanism

#### 11. Submission Requirements
- Documents required for technical bid
- Documents required for financial bid
- Format and packaging instructions

---

## Output Format:

Output a complete, formal tender document in Markdown format.
The document must be:
1. **Professional** - Suitable for government publication
2. **Complete** - All mandatory sections filled
3. **Consistent** - Budget totals must match across sections
4. **Clear** - Unambiguous language suitable for bidders

Do NOT include any meta-commentary. Output ONLY the tender document.

---
""".strip()


def get_final_tender_prompt(
    organization_name: str,
    department_name: str,
    tender_authority: str,
    draft_content: str,
    department_proposals: str,
    publish_date: str
) -> str:
    """
    Get the formatted prompt for generating the final tender document.
    
    Args:
        organization_name: Name of the organization
        department_name: Name of the primary department
        tender_authority: Name/designation of the tender inviting authority
        draft_content: Original markdown content of the draft document
        department_proposals: Consolidated proposals from all relevant departments
        publish_date: Publish date for the tender
        
    Returns:
        Formatted prompt string
    """
    return GENERATE_FINAL_TENDER_PROMPT.format(
        organization_name=organization_name or "Government Organization",
        department_name=department_name or "Department",
        tender_authority=tender_authority or "Executive Engineer",
        draft_content=draft_content,
        department_proposals=department_proposals,
        publish_date=publish_date
    )


def summarize_department_proposals(proposals: list, max_chars_per_proposal: int = 5000) -> str:
    """
    Summarize department proposals to fit within context limits.
    
    When there are many departments, we need to truncate each proposal
    to ensure we don't exceed Gemini's context window.
    
    Args:
        proposals: List of dicts with {department, name, proposal_content}
        max_chars_per_proposal: Maximum characters per proposal (adjusted based on count)
        
    Returns:
        Formatted string with all department proposals
    """
    if not proposals:
        return "No department proposals available."
    
    # Adjust max chars based on number of proposals
    # Total budget: ~100k chars for proposals section
    total_budget = 100000
    num_proposals = len(proposals)
    chars_per_proposal = min(max_chars_per_proposal, total_budget // max(num_proposals, 1))
    
    sections = []
    for i, prop in enumerate(proposals, 1):
        dept = prop.get("department", f"Department {i}")
        name = prop.get("name", "Unknown")
        content = prop.get("proposal_content", "")
        
        # Truncate if needed
        if len(content) > chars_per_proposal:
            content = content[:chars_per_proposal] + "\n\n[... content summarized for context limits ...]"
        
        sections.append(f"""
### Department {i}: {dept}
**Contact:** {name}

{content}

---
""")
    
    return "\n".join(sections)
