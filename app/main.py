from fastapi import FastAPI, HTTPException, UploadFile, File
from schemas import (
    ObligationList,
    Obligation,
    PartyType,
    PenaltyList,
    ImportantDateList,
    RiskFlagList,
)
from extractor import (
    extract_obligations,
    extract_penalties,
    extract_dates,
    extract_risk_flags,
)

app = FastAPI()


# =========================
# HELPERS
# =========================

async def read_text_file(file: UploadFile) -> str:
    if file.content_type != "text/plain":
        raise HTTPException(
            status_code=400,
            detail="Only .txt files are supported"
        )
    try:
        content = await file.read()
        text = content.decode("utf-8")
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Failed to read uploaded file as UTF-8 text"
        )
    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="Uploaded document is empty"
        )
    return text


# =========================
# HEALTH
# =========================

@app.get("/health")
def health():
    return {"status": "ok"}


# =========================
# OBLIGATIONS
# =========================

@app.get("/extract/obligations", response_model=ObligationList)
def extract_obligations_dummy():
    """Phase 2: Schema-only test endpoint"""
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


@app.post("/extract/obligations/from-document", response_model=ObligationList)
async def extract_obligations_from_document(file: UploadFile = File(...)):
    document_text = await read_text_file(file)
    try:
        return extract_obligations(document_text)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


# =========================
# PENALTIES
# =========================

@app.post("/extract/penalties/from-document", response_model=PenaltyList)
async def extract_penalties_from_document(file: UploadFile = File(...)):
    document_text = await read_text_file(file)
    try:
        return extract_penalties(document_text)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


# =========================
# DATES
# =========================

@app.post("/extract/dates/from-document", response_model=ImportantDateList)
async def extract_dates_from_document(file: UploadFile = File(...)):
    document_text = await read_text_file(file)
    try:
        return extract_dates(document_text)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")


# =========================
# RISKS
# =========================

@app.post("/extract/risks/from-document", response_model=RiskFlagList)
async def extract_risks_from_document(file: UploadFile = File(...)):
    document_text = await read_text_file(file)
    try:
        return extract_risk_flags(document_text)
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")
