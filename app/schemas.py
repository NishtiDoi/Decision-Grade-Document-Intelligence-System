from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from enum import Enum
from datetime import date


# =========================
# COMMON ENUMS
# =========================

class PartyType(str, Enum):
    TENANT = "tenant"
    LANDLORD = "landlord"
    BOTH = "both"
    UNKNOWN = "unknown"


class PenaltyType(str, Enum):
    MONETARY = "monetary"
    TERMINATION = "termination"
    LEGAL_ACTION = "legal_action"
    OTHER = "other"


class DateType(str, Enum):
    LEASE_START = "lease_start"
    LEASE_END = "lease_end"
    PAYMENT_DUE = "payment_due"
    NOTICE_DEADLINE = "notice_deadline"
    RENEWAL_DATE = "renewal_date"
    OTHER = "other"


class RiskCategory(str, Enum):
    UNCLEAR_TERMS = "unclear_terms"
    UNUSUAL_PENALTY = "unusual_penalty"
    MISSING_STANDARD_CLAUSE = "missing_standard_clause"
    AMBIGUOUS_RESPONSIBILITY = "ambiguous_responsibility"
    AUTOMATIC_RENEWAL = "automatic_renewal"
    SEVERE_PENALTY = "severe_penalty"
    OTHER = "other"


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# =========================
# OBLIGATIONS
# =========================

class Obligation(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    responsible_party: PartyType
    source_text: str = Field(..., min_length=1, max_length=1000)

    @field_validator("description", "source_text")
    @classmethod
    def not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v.strip()


class ObligationList(BaseModel):
    obligations: list[Obligation] = Field(default_factory=list)


# =========================
# PENALTIES
# =========================

class Penalty(BaseModel):
    description: str = Field(..., min_length=1, max_length=500)
    condition: str = Field(..., min_length=1, max_length=500)
    penalty_type: PenaltyType
    amount: Optional[str] = Field(None, max_length=100)
    source_text: str = Field(..., min_length=1, max_length=1000)

    @field_validator("description", "condition", "source_text")
    @classmethod
    def not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v.strip()

    @field_validator("amount")
    @classmethod
    def normalize_amount(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            return None
        return v.strip() if v else None

    @model_validator(mode="after")
    def enforce_monetary_amount(self):
        if self.penalty_type == PenaltyType.MONETARY and not self.amount:
            raise ValueError("Monetary penalties must include an amount")
        return self


class PenaltyList(BaseModel):
    penalties: list[Penalty] = Field(default_factory=list)


# =========================
# IMPORTANT DATES
# =========================

class ImportantDate(BaseModel):
    event_description: str = Field(..., min_length=1, max_length=500)
    date_type: DateType
    date_value: Optional[date] = None
    relative_description: Optional[str] = Field(None, max_length=500)
    source_text: str = Field(..., min_length=1, max_length=1000)

    @field_validator("event_description", "source_text")
    @classmethod
    def not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v.strip()

    @field_validator("relative_description")
    @classmethod
    def normalize_relative(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            return None
        return v.strip() if v else None

    @model_validator(mode="after")
    def validate_date_logic(self):
        if self.date_value is None and not self.relative_description:
            raise ValueError(
                "Either date_value or relative_description must be provided"
            )
        return self


class ImportantDateList(BaseModel):
    dates: list[ImportantDate] = Field(default_factory=list)


# =========================
# RISK FLAGS
# =========================

class RiskFlag(BaseModel):
    risk_category: RiskCategory
    description: str = Field(..., min_length=1, max_length=500)
    confidence: ConfidenceLevel
    source_text: str = Field(..., min_length=1, max_length=1000)

    @field_validator("description", "source_text")
    @classmethod
    def not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field cannot be empty or whitespace")
        return v.strip()

    @field_validator("description")
    @classmethod
    def forbid_advice_language(cls, v: str) -> str:
        forbidden_phrases = [
            "you should",
            "you must",
            "this is illegal",
            "this violates",
            "lawsuit",
            "sue",
            "dangerous",
            "terrible",
            "unfair",
        ]
        lv = v.lower()
        for phrase in forbidden_phrases:
            if phrase in lv:
                raise ValueError(
                    f"Risk description contains forbidden language: '{phrase}'"
                )
        return v


class RiskFlagList(BaseModel):
    risk_flags: list[RiskFlag] = Field(default_factory=list)
