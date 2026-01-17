from fastapi import FastAPI
from schemas import ObligationList, Obligation, PartyType

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/extract/obligations", response_model=ObligationList)
def extract_obligations_dummy():
    """
    Phase 2: Returns hardcoded, schema-valid obligations.
    No LLM. Just proving the schema works.
    """
    return ObligationList(
        obligations=[
            Obligation(
                description="Pay rent by the 5th of each month",
                responsible_party=PartyType.TENANT,
                source_text="Tenant shall pay rent on or before the 5th day of each calendar month."
            ),
            Obligation(
                description="Maintain heating and plumbing in working order",
                responsible_party=PartyType.LANDLORD,
                source_text="Landlord agrees to keep all heating, plumbing, and electrical systems in good repair."
            ),
        ]
    )