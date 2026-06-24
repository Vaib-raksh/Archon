import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq()

def clean_json(raw: str) -> str:
    return re.sub(r"```json|```", "", raw).strip()

def call_groq(system_prompt: str, user_content: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.2,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
    )
    return response.choices[0].message.content.strip()


# ── UI SCHEMA ──────────────────────────────────────────────
UI_PROMPT = """You are a UI architect.
Generate a UI schema from the given system design.

Return ONLY valid JSON with exactly this structure:
{
  "pages": [
    {
      "name": "string",
      "route": "string",
      "layout": "auth | dashboard | full",
      "components": [
        {
          "type": "form | table | card | chart | navbar | sidebar",
          "id": "string",
          "fields": [
            {
              "name": "string",
              "type": "text | email | password | number | select | checkbox",
              "label": "string",
              "required": true
            }
          ],
          "actions": ["string"]
        }
      ]
    }
  ]
}
Return ONLY JSON. No explanation. No markdown."""

# ── API SCHEMA ─────────────────────────────────────────────
API_PROMPT = """You are a backend API architect.
Generate a REST API schema from the given system design.

Return ONLY valid JSON with exactly this structure:
{
  "endpoints": [
    {
      "method": "GET | POST | PUT | DELETE",
      "path": "string",
      "description": "string",
      "auth_required": true,
      "allowed_roles": ["string"],
      "request_body": {
        "fields": [
          {"name": "string", "type": "string", "required": true}
        ]
      },
      "response": {
        "fields": [
          {"name": "string", "type": "string"}
        ]
      }
    }
  ]
}
Return ONLY JSON. No explanation. No markdown."""

# ── DB SCHEMA ──────────────────────────────────────────────
DB_PROMPT = """You are a database architect.
Generate a SQL database schema from the given system design.

Return ONLY valid JSON with exactly this structure:
{
  "tables": [
    {
      "name": "string",
      "columns": [
        {
          "name": "string",
          "type": "UUID | VARCHAR | TEXT | INTEGER | FLOAT | BOOLEAN | TIMESTAMP",
          "primary_key": false,
          "nullable": false,
          "foreign_key": {
            "table": "string",
            "column": "string"
          }
        }
      ],
      "indexes": ["string"]
    }
  ]
}
- foreign_key is optional, only include when column references another table
- indexes should be column names worth indexing
Return ONLY JSON. No explanation. No markdown."""

# ── AUTH SCHEMA ────────────────────────────────────────────
AUTH_PROMPT = """You are a security architect.
Generate an auth and permissions schema from the given system design.

Return ONLY valid JSON with exactly this structure:
{
  "auth_type": "jwt",
  "token_expiry": "string",
  "roles": [
    {
      "name": "string",
      "permissions": ["string"]
    }
  ],
  "route_guards": [
    {
      "route": "string",
      "allowed_roles": ["string"],
      "redirect_to": "string"
    }
  ]
}
Return ONLY JSON. No explanation. No markdown."""


def generate_schemas(design: dict) -> dict:
    design_str = json.dumps(design)
    schemas = {}
    failed = []

    # UI Schema
    try:
        raw = call_groq(UI_PROMPT, f"System design: {design_str}")
        schemas["ui"] = json.loads(clean_json(raw))
    except json.JSONDecodeError:
        failed.append("ui")
        schemas["ui"] = {"error": "parse_failed", "raw": raw}

    # API Schema
    try:
        raw = call_groq(API_PROMPT, f"System design: {design_str}")
        schemas["api"] = json.loads(clean_json(raw))
    except json.JSONDecodeError:
        failed.append("api")
        schemas["api"] = {"error": "parse_failed", "raw": raw}

    # DB Schema
    try:
        raw = call_groq(DB_PROMPT, f"System design: {design_str}")
        schemas["db"] = json.loads(clean_json(raw))
    except json.JSONDecodeError:
        failed.append("db")
        schemas["db"] = {"error": "parse_failed", "raw": raw}

    # Auth Schema
    try:
        raw = call_groq(AUTH_PROMPT, f"System design: {design_str}")
        schemas["auth"] = json.loads(clean_json(raw))
    except json.JSONDecodeError:
        failed.append("auth")
        schemas["auth"] = {"error": "parse_failed", "raw": raw}

    schemas["failed_schemas"] = failed
    return schemas


if __name__ == "__main__":
    import sys
    sys.path.append("..")
    from stage1_intent import extract_intent
    from stage2_design import design_system

    prompt = "Build a CRM with login, contacts, dashboard, and admin analytics"
    intent = extract_intent(prompt)
    design = design_system(intent)

    print("--- Stage 3: Generating 4 schemas ---")
    schemas = generate_schemas(design)

    for key in ["ui", "api", "db", "auth"]:
        print(f"\n=== {key.upper()} SCHEMA ===")
        print(json.dumps(schemas[key], indent=2))

    if schemas["failed_schemas"]:
        print(f"\n Failed schemas: {schemas['failed_schemas']}")
    else:
        print("\n All 4 schemas generated successfully")