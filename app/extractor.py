import os
import json
from dotenv import load_dotenv
from google import genai

from schemas import (
    ObligationList,
    PenaltyList,
    ImportantDateList,
    RiskFlagList,
)

# ------------------------------------------------------------------
# Setup
# ------------------------------------------------------------------

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("GOOGLE_API_KEY not found in environment")

client = genai.Client(api_key=API_KEY)

MODEL_ID = "gemini-flash-latest"


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def clean_gemini_json(text: str) -> str:
    """
    Gemini sometimes wraps JSON in markdown or adds text.
    This function aggressively extracts the JSON object.
    """
    text = text.strip()

    # Remove markdown fences if present
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("{"):
                text = part
                break

    # Trim before first '{'
    if "{" in text:
        text = text[text.index("{"):]

    # Trim after last '}'
    if "}" in text:
        text = text[: text.rindex("}") + 1]

    return text


def call_gemini(prompt: str) -> dict:
    """
    Single Gemini call.
    Returns parsed JSON or crashes.
    """
    response = client.models.generate_content(
        model=MODEL_ID,
        contents=prompt,
        config={
            "temperature": 0,
            "max_output_tokens": 4096,
        },
    )

    raw_text = response.text
    cleaned = clean_gemini_json(raw_text)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print("RAW RESPONSE:")
        print(raw_text)
        raise ValueError(f"Gemini returned invalid JSON: {e}")


# ------------------------------------------------------------------
# Obligations
# ------------------------------------------------------------------

def extract_obligations(document_text: str) -> ObligationList:
    prompt = f"""
You are extracting obligations from a rental agreement.

RULES:
1. Extract ONLY obligations explicitly stated
2. Do NOT infer or guess
3. Identify responsible party: tenant, landlord, both, or unknown
4. Include exact source text

Return ONLY valid JSON in this format:
{{
  "obligations": [
    {{
      "description": "...",
      "responsible_party": "tenant|landlord|both|unknown",
      "source_text": "..."
    }}
  ]
}}

DOCUMENT:
{document_text}
"""

    data = call_gemini(prompt)
    result = ObligationList(**data)

    if not result.obligations:
        raise ValueError("No obligations extracted")

    return result


# ------------------------------------------------------------------
# Penalties
# ------------------------------------------------------------------

def extract_penalties(document_text: str) -> PenaltyList:
    prompt = f"""
You are extracting penalty clauses from a rental agreement.

RULES:
1. Extract ONLY penalties explicitly stated
2. Clearly state what triggers the penalty
3. Do NOT guess amounts
4. If vague, SKIP IT

Return ONLY valid JSON:
{{
  "penalties": [
    {{
      "description": "...",
      "condition": "...",
      "penalty_type": "monetary|termination|legal_action|other",
      "amount": "... or null",
      "source_text": "..."
    }}
  ]
}}

DOCUMENT:
{document_text}
"""

    data = call_gemini(prompt)
    result = PenaltyList(**data)

    return result


# ------------------------------------------------------------------
# Important Dates
# ------------------------------------------------------------------

def extract_dates(document_text: str) -> ImportantDateList:
    prompt = f"""
You are extracting important dates from a rental agreement.

RULES:
1. Extract ONLY explicitly stated dates
2. Use ISO format YYYY-MM-DD if specific
3. For recurring dates, set date_value = null
4. Do NOT guess or convert relative dates

Return ONLY valid JSON:
{{
  "dates": [
    {{
      "event_description": "...",
      "date_type": "lease_start|lease_end|payment_due|notice_deadline|other",
      "date_value": "YYYY-MM-DD or null",
      "relative_description": "... or null",
      "source_text": "..."
    }}
  ]
}}

DOCUMENT:
{document_text}
"""

    data = call_gemini(prompt)
    result = ImportantDateList(**data)

    return result


# ------------------------------------------------------------------
# Risk Flags
# ------------------------------------------------------------------

def extract_risk_flags(document_text: str) -> RiskFlagList:
    prompt = f"""
You are identifying potential risks in a rental agreement.

CRITICAL RULES:
1. Flag ONLY risks based on specific clauses
2. NO legal advice
3. NO emotional language
4. Use predefined categories only
5. Explicitly mark confidence: high|medium|low

Return ONLY valid JSON:
{{
  "risk_flags": [
    {{
      "risk_category": "unclear_terms|unusual_penalty|missing_standard_clause|ambiguous_responsibility|automatic_renewal|severe_penalty|other",
      "description": "factual description",
      "confidence": "high|medium|low",
      "source_text": "exact clause"
    }}
  ]
}}

DOCUMENT:
{document_text}
"""

    data = call_gemini(prompt)
    result = RiskFlagList(**data)

    return result
