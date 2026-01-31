import os
import json
import re
from typing import Dict, Any
from dotenv import load_dotenv
from google import genai
from google.genai import types

from schemas import (
    ObligationList,
    PenaltyList,
    ImportantDateList,
    RiskFlagList,
)

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("GOOGLE_API_KEY not found in environment")

client = genai.Client(api_key=API_KEY)
MODEL_ID = "gemini-flash-latest"

# --- HELPERS ---
def clean_gemini_json(text: str) -> str:
    text = text.strip()
    if "```" in text:
        matches = re.findall(r"```(?:json)?(.*?)```", text, re.DOTALL)
        if matches: text = matches[0].strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1: text = text[start : end + 1]
    return text

def call_gemini(prompt: str) -> Dict[str, Any]:
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0,
                response_mime_type="application/json",
                max_output_tokens=8192,
            )
        )
        cleaned = clean_gemini_json(response.text)
        try:
            return json.loads(cleaned)
        except:
            return json.loads(cleaned.replace('\n', ' '))
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return {}

# --- OBLIGATIONS (Refined Exclusion) ---
def extract_obligations(document_text: str) -> ObligationList:
    prompt = f"""
    You are extracting obligations from a rental agreement.

    RULES:
    1. Extract active duties (e.g., "Tenant shall pay rent", "Landlord must maintain").
    2. Identify responsible party: tenant, landlord, both, or unknown.
    3. Include exact source text.
    4. INCLUDE: Recurring financial obligations (Rent, Maintenance).
    5. EXCLUDE: Conditional penalties (late fees).
    6. EXCLUDE: One-time deductions from security deposit (like painting charges). These are Penalties.

    Return ONLY valid JSON:
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
    if not data or "obligations" not in data: return ObligationList(obligations=[])
    return ObligationList(**data)

# --- PENALTIES (Refined Types) ---
def extract_penalties(document_text: str) -> PenaltyList:
    prompt = f"""
    You are extracting penalty clauses.

    RULES:
    1. Extract explicitly stated penalties and mandatory deductions (painting charges).
    2. CLASSIFICATION RULE: If the penalty involves rights (e.g. "hold possession"), set penalty_type to 'other'.
    3. AMOUNT RULE: If monetary, write the exact amount. If it's a right (like holding possession), write 'Retention of possession'.
    4. Truncate 'amount' descriptions to be short (max 100 chars).

    Return ONLY valid JSON:
    {{
      "penalties": [
        {{
          "description": "...",
          "condition": "...",
          "penalty_type": "monetary|termination|legal_action|other",
          "amount": "Short amount or 'Not specified'",
          "source_text": "..."
        }}
      ]
    }}
    DOCUMENT:
    {document_text}
    """
    data = call_gemini(prompt)
    if not data or "penalties" not in data: return PenaltyList(penalties=[])
    
    # Sanitize
    for p in data["penalties"]:
        if p.get("amount") is None:
            if "monetary" in p.get("penalty_type", ""): p["amount"] = "Not specified"
        else:
            s_amount = str(p["amount"])
            if len(s_amount) > 100: p["amount"] = s_amount[:97] + "..."
            
    return PenaltyList(**data)

# --- DATES ---
def extract_dates(document_text: str) -> ImportantDateList:
    prompt = f"""
    You are extracting dates.
    RULES:
    1. Extract explicit dates (ISO format YYYY-MM-DD).
    2. Recurring dates: date_value = null.
    
    Return ONLY valid JSON:
    {{
      "dates": [
        {{
          "event_description": "...",
          "date_type": "lease_start|lease_end|payment_due|notice_deadline|other",
          "date_value": "YYYY-MM-DD or null",
          "relative_description": "...",
          "source_text": "..."
        }}
      ]
    }}
    DOCUMENT:
    {document_text}
    """
    data = call_gemini(prompt)
    if not data or "dates" not in data: return ImportantDateList(dates=[])
    return ImportantDateList(**data)

# --- RISKS ---
def extract_risk_flags(document_text: str) -> RiskFlagList:
    prompt = f"""
    You are identifying risks.
    RULES:
    1. Flag specific clauses only.
    2. Use predefined categories.
    
    Return ONLY valid JSON:
    {{
      "risk_flags": [
        {{
          "risk_category": "unclear_terms|unusual_penalty|missing_standard_clause|ambiguous_responsibility|automatic_renewal|severe_penalty|other",
          "description": "...",
          "confidence": "high|medium|low",
          "source_text": "..."
        }}
      ]
    }}
    DOCUMENT:
    {document_text}
    """
    data = call_gemini(prompt)
    if not data or "risk_flags" not in data: return RiskFlagList(risk_flags=[])
    return RiskFlagList(**data)