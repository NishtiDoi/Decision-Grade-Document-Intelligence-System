from pydantic import BaseModel, Field, field_validator ## BaseModel: turns python class into validated data model
# field: adds constraints to fields 
# field_validator: custom validation logic for fields
from typing import Literal # Restricts a value to a specific set of literals
from enum import Enum # Defines enumerations, a set of symbolic names bound to unique, constant values

class PartyType(str, Enum):  ## Custom type called PartyType
    """Who has this obligation?"""
    TENANT = "tenant"
    LANDLORD = "landlord"
    BOTH = "both"
    UNKNOWN = "unknown"

class Obligation(BaseModel):
    """
    A single extracted obligation from a rental agreement.
    Validation rules:
    - description must not be empty
    - responsible_party must be one of the defined PartyType values
    - source_text must not be empty (proves it exists in the doc)
    """
    description: str = Field(
        ..., 
        min_length=1, 
        max_length=500,
        description="Description of the what party must do"
    )
    responsible_party: PartyType = Field(
        ...,
        description="Who has this obligation?"
    )
    source_text: str = Field(
        ..., 
        min_length=1,
        max_length=1000,
        description="The exact text from the document that supports this obligation"
    )

    @field_validator('description')
    @classmethod
    def description_must_not_be_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Description cannot be empty or whitespace")
        return v.strip()
    
    @field_validator('source_text')
    @classmethod
    def source_must_not_be_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Source text cannot be empty or whitespace")
        return v.strip()


class ObligationList(BaseModel):
    """Container for all extracted obligations"""
    obligations: list[Obligation] = Field(default_factory=list)