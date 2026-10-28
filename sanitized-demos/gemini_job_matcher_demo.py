"""
SANITIZED EDUCATIONAL DEMO: Structured AI Job Matching Engine
Author: Brian Cummings | Portfolio: applied-ai-operations-portfolio

PLAIN-ENGLISH SUMMARY FOR NON-TECHNICAL REVIEWERS:
Instead of letting an AI chatbot write a freeform paragraph (where it might guess
or invent details), this script locks Google's Gemini API into a strict checklist.
It reads a messy job posting, extracts the exact hourly pay and requirements,
flags potential employment barriers, and outputs a verified 0-100 match score.
"""

import os
from typing import List, Optional
from pydantic import BaseModel, Field
from google import genai


# 1. DEFINE THE STRICT DATA CONTRACT (The AI cannot deviate from this structure)
class JobMatchScorecard(BaseModel):
    job_title: str = Field(description="Standardized job title from the posting.")
    employer_name: str = Field(description="Hiring company or organization name.")
    match_score: int = Field(description="0 to 100 suitability score for entry-to-mid level candidates.")
    hourly_wage_min: Optional[float] = Field(description="Starting hourly pay in USD. Must be null if not stated.")
    hourly_wage_max: Optional[float] = Field(description="Maximum hourly pay in USD. Must be null if not stated.")
    transit_accessible: bool = Field(description="True if reachable via municipal bus route or central corridor.")
    barrier_flags: List[str] = Field(description="Explicit requirements: e.g., 'Heavy Lifting 50lbs', 'CDL Required'.")
    staff_summary: str = Field(description="Two-sentence plain-English summary for the job developer.")


def evaluate_job_posting(raw_job_text: str, candidate_profile: str) -> str:
    # 2. LOAD API CREDENTIALS SECURELY FROM ENVIRONMENT (Zero hardcoded keys)
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("Missing GEMINI_API_KEY environment variable.")

    client = genai.Client(api_key=api_key)

    # 3. BUILD THE FACT-LOCKED PROMPT (Instructs AI to return null rather than guess)
    prompt = f"""
    You are an operations workforce analyst. Evaluate the raw job posting below
    against our candidate profile. Do NOT guess missing wages; return null if unlisted.

    CANDIDATE PROFILE: {candidate_profile}
    RAW JOB POSTING: {raw_job_text}
    """

    # 4. CALL GEMINI 3.8 FLASH WITH STRICT JSON SCHEMA ENFORCEMENT
    interaction = client.interactions.create(
        model="gemini-3.8-flash",
        input=prompt,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": JobMatchScorecard.model_json_schema(),
        },
    )
    return interaction.output_text


if __name__ == "__main__":
    # 5. SYNTHETIC DEMONSTRATION INPUT (100% fictional listing for safe testing)
    sample_post = (
        " hiring immediately: Inventory & Receiving Associate at North Valley Supply (Redding, CA). "
        "$21.50 - $24.00/hr. Full-time, Mon-Fri 7:00am-3:30pm. Located 1 block from RABA Route 4 bus stop. "
        "Duties: scan incoming freight, update warehouse tablet, lift up to 40 lbs. No degree required; "
        "paid on-the-job training provided during your first two weeks."
    )
    sample_candidate = "Warehouse & retail background; relies on public transit; needs daytime schedule; $20/hr minimum."
    print(evaluate_job_posting(sample_post, sample_candidate))
