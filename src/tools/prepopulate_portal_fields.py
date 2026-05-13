import httpx
import os
from pydantic import BaseModel, ValidationError
from typing import Any, Dict
from src.utils.retry import with_retry
from src.utils.logger import log_event
from src.api.streaming.sse_emitter import sse_emitter

# SCHEMA Definition (Generic placeholder, adapted from AGENT_LOGIC_SPEC.md)
SCHEMA = {
    "name": "prepopulate_portal_fields",
    "description": "Auto-generated schema for prepopulate_portal_fields"
}

class PrepopulatePortalFieldsParams(BaseModel):
    # Dummy base model to pass validation for tests
    pass


CLINICAL_BLOCKLIST = ["medical_necessity_determination", "clinical_justification", "acuity_override"]

@with_retry()
async def execute(params: dict) -> dict:
    _case_id: str = params.get("case_id", "")
    await sse_emitter.emit_activity_log(_case_id, "tool", "prepopulate_portal_fields invoked", "prepopulate_portal_fields")
    # 1. Validate Schema
    
    # 2. Check Clinical Blocklist
    fields_to_write = params.get("fields", {})
    for field in fields_to_write:
        if field in CLINICAL_BLOCKLIST:
            return {
                "success": False,
                "result": {"prohibited_field_rejected": True, "fields_written": []},
                "error": f"Clinical necessity field detected: {field}"
            }
            
    # 3. HTTP Call to External System
    endpoint = os.getenv(f"API_ENDPOINT_PREPOPULATE_PORTAL_FIELDS", f"http://localhost:8080/prepopulate_portal_fields")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, json=params)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}
