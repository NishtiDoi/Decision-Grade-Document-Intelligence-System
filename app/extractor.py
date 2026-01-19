import os 
import json 
import google.generativeai as genai
from dotenv import load_dotenv
from schemas import ObligationList, PartyType

load_dotenv()  # Load environment variables from .env file

genai.configure(api_key=os.getenv("GOOGLE_API_KEY")) # Configure the GenAI client with the API key

model=genai.GenerativeModel(
    model_name="gemini-flash-latest"
)

def extract_obligations(document_text: str) -> ObligationList:
    """
    Extract obligations using Gemini
    
    :param document_text: Description
    :type document_text: str
    :return: Description
    :rtype: Any
    """

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
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0,
                "response_mime_type": "application/json"
            }
        )

        response_text=response.text
        response_json=json.loads(response_text)

        return ObligationList(**response_json)
    
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON response: {e}")
    
    except Exception as e:
        raise 