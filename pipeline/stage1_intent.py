import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq()

SYSTEM_PROMPT = """You are an expert software architect. 
Extract structured intent from a user's app description.

Return ONLY valid JSON with exactly this structure:
{
  "app_name": "string",
  "app_type": "string",
  "features": ["string"],
  "pages": ["string"],
  "roles": ["string"],
  "entities": ["string"],
  "integrations": ["string"],
  "assumptions": ["string"]
}

Rules:
- features: main capabilities (e.g. "user login", "contact management")
- pages: UI pages needed (e.g. "Login", "Dashboard", "Contacts")
- roles: user types (e.g. "admin", "user", "guest")
- entities: database objects (e.g. "User", "Contact", "Invoice")
- integrations: external services if mentioned (e.g. "Stripe", "Gmail")
- assumptions: anything you assumed that wasn't stated
- Return ONLY the JSON. No explanation. No markdown. No extra text.
"""

def extract_intent(user_prompt: str) -> dict:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"App description: {user_prompt}"}
        ]
    )
    
    raw = response.choices[0].message.content.strip()
    
    # Cleanup if model adds markdown fences 
    raw = re.sub(r"```json|```", "", raw).strip()
    
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        # If JSON is broken,return a safe fallback with the error note
        result = {
            "app_name": "Unknown",
            "app_type": "Unknown",
            "features": [],
            "pages": [],
            "roles": ["user"],
            "entities": [],
            "integrations": [],
            "assumptions": ["Stage 1 failed to parse — raw output saved for repair"],
            "raw_fallback": raw
        }
    
    return result


# Quick test 
if __name__ == "__main__":
    test_prompt = "Build a CRM with login, contacts, dashboard, and admin analytics"
    result = extract_intent(test_prompt)
    print(json.dumps(result, indent=2))