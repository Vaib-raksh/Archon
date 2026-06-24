import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq()

SYSTEM_PROMPT = """You are an expert software architect.
Given structured app intent, design the full system architecture.

Return ONLY valid JSON with exactly this structure:
{
  "entities": [
    {
      "name": "string",
      "fields": [
        {"name": "string", "type": "string", "required": true}
      ],
      "relations": [
        {"to": "string", "type": "one-to-many | many-to-many | one-to-one"}
      ]
    }
  ],
  "pages": [
    {
      "name": "string",
      "route": "string",
      "allowed_roles": ["string"],
      "components": ["string"]
    }
  ],
  "flows": [
    {
      "name": "string",
      "steps": ["string"]
    }
  ],
  "auth": {
    "type": "jwt | session | oauth",
    "roles": ["string"],
    "protected_routes": ["string"]
  }
}

Rules:
- Every entity must have an "id" field of type "uuid"
- Every entity must have "created_at" of type "timestamp"
- fields type must be one of: uuid, string, text, integer, float, boolean, timestamp
- relations must reference entity names that exist in the entities list
- protected_routes must match routes defined in pages
- Return ONLY the JSON. No explanation. No markdown. No extra text.
"""

def design_system(intent: dict) -> dict:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"App intent: {json.dumps(intent)}"}
        ]
    )

    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"```json|```", "", raw).strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "entities": [],
            "pages": [],
            "flows": [],
            "auth": {
                "type": "jwt",
                "roles": ["user"],
                "protected_routes": []
            },
            "assumptions": ["Stage 2 failed to parse — raw output saved for repair"],
            "raw_fallback": raw
        }

    return result


if __name__ == "__main__":
    # Uses Stage 1 output as input
    from stage1_intent import extract_intent
    
    test_prompt = "Build a CRM with login, contacts, dashboard, and admin analytics"
    intent = extract_intent(test_prompt)
    
    print("--- Stage 1 output ---")
    print(json.dumps(intent, indent=2))
    
    result = design_system(intent)
    print("\n--- Stage 2 output ---")
    print(json.dumps(result, indent=2))