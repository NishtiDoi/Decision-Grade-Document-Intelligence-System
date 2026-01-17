import os 
import json 
import google.generativeai as genai
from dotenv import load_dotenv
from schemas import Obligation, PartyType

load_dotenv()  # Load environment variables from .env file