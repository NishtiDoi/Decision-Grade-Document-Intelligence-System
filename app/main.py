from fastapi import FastAPI, HTTPException, UploadFile, File
from schemas import ObligationList, Obligation, PartyType
from extractor import extract_obligations

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

@app.post("/extract/obligations/from-document", response_model=ObligationList)
async def extract_obligations_from_document(file: UploadFile = File(...)):
    """
    Phase 3: Extract obligations from uploaded document using LLM.    
    :param file: Description
    :type file: UploadFile
    Accepts: .txt files
    Returns: Validated obligations or fails loudly
    """

    try:
        content=await file.read()
        document_text=content.decode("utf-8")
    except  Exception as e:
        raise HTTPException(status_code=400, detail="Failed to read uploaded file. Ensure it's a valid text file.") 
    
    if not document_text.strip():
        raise HTTPException(status_code=400, detail="Uploaded document is empty.")
    
    try:
        result=extract_obligations(document_text)
        return result
    except ValueError as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: ] {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
    
@app.get("/test/invalid-obligations")
def test_invalid_obligation():
    """
    Phase 2: Schema validation test (keep for testing purposes)
    """
    try:
        bad_obligation=Obligation(
            description="   ",  # Invalid: only whitespace
            responsible_party="invalid_party",  # Invalid: not in PartyType
            source_text="Some text"
        )
        return {"error": "Validation should have failed but didn't."}
    except Exception as e:
        return {
            "expected": "Schema validation failure",
            "error": str(e),
            "status": "✅ Validation working"
        }