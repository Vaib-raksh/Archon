import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq()

def clean_json(raw: str) -> str:
    return re.sub(r"```json|```", "", raw).strip()


# ── VALIDATION RULE────────────────────────

def validate_ui(schemas: dict) -> list:
    errors = []
    ui = schemas.get("ui", {})
    api = schemas.get("api", {})

    api_paths = [e["path"] for e in api.get("endpoints", [])]
    
    for page in ui.get("pages", []):
        for component in page.get("components", []):
            for action in component.get("actions", []):
                # Check every UI action maps to a real API endpoint
                matched = any(action in path for path in api_paths)
                if not matched:
                    errors.append({
                        "schema": "ui",
                        "error": f"UI action '{action}' on page '{page['name']}' has no matching API endpoint",
                        "type": "missing_api_mapping"
                    })
    return errors


def validate_api(schemas: dict) -> list:
    errors = []
    api = schemas.get("api", {})
    db = schemas.get("db", {})
    auth = schemas.get("auth", {})

    db_tables = [t["name"].lower() for t in db.get("tables", [])]
    auth_roles = [r["name"] for r in auth.get("roles", [])]

    for endpoint in api.get("endpoints", []):
        # Check every API role exists in auth schema
        for role in endpoint.get("allowed_roles", []):
            if role not in auth_roles:
                errors.append({
                    "schema": "api",
                    "error": f"Endpoint '{endpoint['path']}' uses role '{role}' not defined in auth schema",
                    "type": "missing_role"
                })

        # Check endpoint path references a real DB table
        path_parts = endpoint["path"].strip("/").split("/")
        if path_parts:
            resource = path_parts[0].lower().rstrip("s")  # crude singularize
            if resource and not any(resource in t for t in db_tables):
                errors.append({
                    "schema": "api",
                    "error": f"Endpoint '{endpoint['path']}' references resource '{resource}' with no matching DB table",
                    "type": "missing_db_table"
                })
    return errors


def validate_db(schemas: dict) -> list:
    errors = []
    db = schemas.get("db", {})
    design = schemas.get("_design", {})

    table_names = [t["name"].lower() for t in db.get("tables", [])]
    entity_names = [e["name"].lower() for e in design.get("entities", [])]

    # Every entity should have a DB table
    for entity in entity_names:
        if entity not in table_names:
            errors.append({
                "schema": "db",
                "error": f"Entity '{entity}' from system design has no DB table",
                "type": "missing_table"
            })

    #foreign keys reference real tables
    for table in db.get("tables", []):
        for col in table.get("columns", []):
            fk = col.get("foreign_key")
            if fk and fk.get("table", "").lower() not in table_names:
                errors.append({
                    "schema": "db",
                    "error": f"Foreign key in '{table['name']}.{col['name']}' references non-existent table '{fk['table']}'",
                    "type": "invalid_foreign_key"
                })
    return errors


def validate_auth(schemas: dict) -> list:
    errors = []
    auth = schemas.get("auth", {})
    ui = schemas.get("ui", {})

    ui_routes = [p["route"] for p in ui.get("pages", [])]
    
    for guard in auth.get("route_guards", []):
        if guard["route"] not in ui_routes:
            errors.append({
                "schema": "auth",
                "error": f"Route guard for '{guard['route']}' has no matching UI page",
                "type": "missing_route"
            })
    return errors


# ── REPAIR ENGINe─────────────────────

REPAIR_PROMPT = """You are a schema repair engine.
A schema has validation errors. Fix ONLY the issues listed.
Return the corrected schema as valid JSON only.
Do not change anything that isn't broken.
Return ONLY JSON. No explanation. No markdown."""

def repair_schema(schema_name: str, schema: dict, errors: list) -> dict:
    error_summary = "\n".join([f"- {e['error']}" for e in errors])
    
    prompt = f"""Schema type: {schema_name}
Current schema:
{json.dumps(schema, indent=2)}

Errors to fix:
{error_summary}

Return the fixed schema as valid JSON."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        messages=[
            {"role": "system", "content": REPAIR_PROMPT},
            {"role": "user", "content": prompt}
        ]
    )

    raw = response.choices[0].message.content.strip()
    raw = clean_json(raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": "repair_failed", "original": schema}


# ── MAIN VALIDATE + REPAIR LOOP─────────

def validate_and_repair(schemas: dict, design: dict, max_retries: int = 2) -> dict:
    schemas["_design"] = design
    report = {
        "total_errors": 0,
        "repaired": [],
        "repair_failed": [],
        "passes": 0
    }

    for attempt in range(max_retries):
        report["passes"] += 1
        all_errors = []

        all_errors += validate_ui(schemas)
        all_errors += validate_api(schemas)
        all_errors += validate_db(schemas)
        all_errors += validate_auth(schemas)

        if not all_errors:
            print(f" Validation passed on attempt {attempt + 1}")
            break

        print(f"Attempt {attempt + 1}: Found {len(all_errors)} error(s) — repairing...")

        # Group errors by schema
        errors_by_schema = {}
        for e in all_errors:
            errors_by_schema.setdefault(e["schema"], []).append(e)

        # Repair only broken schemas
        for schema_name, errors in errors_by_schema.items():
            print(f"   Repairing {schema_name} schema ({len(errors)} error(s))...")
            repaired = repair_schema(schema_name, schemas[schema_name], errors)

            if "error" in repaired and repaired["error"] == "repair_failed":
                report["repair_failed"].append(schema_name)
            else:
                schemas[schema_name] = repaired
                report["repaired"].append(schema_name)

        report["total_errors"] += len(all_errors)

    # Clean up internal key
    del schemas["_design"]
    schemas["_validation_report"] = report
    return schemas


if __name__ == "__main__":
    import sys
    sys.path.append("..")
    from stage1_intent import extract_intent
    from stage2_design import design_system
    from stage3_schemas import generate_schemas

    prompt = "Build a CRM with login, contacts, dashboard, and admin analytics"

    print("Running full pipeline...\n")
    intent = extract_intent(prompt)
    design = design_system(intent)
    schemas = generate_schemas(design)
    final = validate_and_repair(schemas, design)

    print("\n--- Validation Report ---")
    print(json.dumps(final["_validation_report"], indent=2))
    print("\n Pipeline complete!")