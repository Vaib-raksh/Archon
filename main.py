import json
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from pipeline.stage1_intent import extract_intent
from pipeline.stage2_design import design_system
from pipeline.stage3_schemas import generate_schemas
from pipeline.stage4_validate import validate_and_repair

app = FastAPI(title="Archon", description="Natural language to app schema")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="frontend"), name="static")

class PromptRequest(BaseModel):
    prompt: str

@app.get("/")
def serve_frontend():
    return FileResponse("frontend/index.html")

@app.post("/generate")
def generate(request: PromptRequest):
    start = time.time()
    result = {}

    # Stage 1
    print(f"\n[Archon] Running Stage 1 — Intent Extraction")
    intent = extract_intent(request.prompt)
    result["intent"] = intent

    # Stage 2
    print(f"[Archon] Running Stage 2 — System Design")
    design = design_system(intent)
    result["design"] = design

    # Stage 3
    print(f"[Archon] Running Stage 3 — Schema Generation")
    schemas = generate_schemas(design)
    result["schemas"] = schemas

    # Stage 4
    print(f"[Archon] Running Stage 4 — Validate + Repair")
    final_schemas = validate_and_repair(schemas, design)
    result["schemas"] = final_schemas

    result["meta"] = {
        "prompt": request.prompt,
        "latency_seconds": round(time.time() - start, 2),
        "validation_report": final_schemas.get("_validation_report", {})
    }

    print(f"[Archon] Done in {result['meta']['latency_seconds']}s")
    return result

@app.get("/health")
def health():
    return {"status": "ok", "service": "Archon"}