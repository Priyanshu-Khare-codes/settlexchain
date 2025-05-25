from google import genai
from dotenv import load_dotenv
from decimal import Decimal
import json
import os

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

base_prompts = [
    "You are a helpful AI financial assistant who works for the company 'SettleXChain' and you are made by the team 'Algorythm Artist'.",
    "Your work is to help the user manage their expense records which are stored on the BNB blockchain.",
    "You compute the payments of the different members: who paid to whom, how much a user paid, who paid the highest, and track  etc."
]

client = genai.Client(api_key=GOOGLE_API_KEY)  # 🔧 Fixed: use the actual env var, not string literal

# 🧙 Magic function to handle Decimals
def decimal_to_float(obj):
    if isinstance(obj, list):
        return [decimal_to_float(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return float(obj)
    return obj

def get_ai_response(user_input, expenses):
    expenses_clean = decimal_to_float(expenses)  # 💡 Clean up those Decimals

    prompts = base_prompts.copy()
    prompts.append(json.dumps(expenses_clean))  # ✅ Now it's safe to serialize
    prompts.append(user_input)

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompts
    )
    result = response.text
    return result

        