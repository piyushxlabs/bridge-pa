"""
Routes for the VeeaHub Mock Proxy.
We define catch-all or specific routes for the endpoints called by src/tools/.
"""
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/{endpoint_name}")
@router.get("/{endpoint_name}")
async def handle_tool_request(endpoint_name: str, request: Request):
    """
    Catch-all endpoint for all mocked tool interactions.
    """
    # Specifically for write_phi_audit_log, return the expected success format
    if endpoint_name == "write_phi_audit_log":
        return JSONResponse(status_code=200, content={
            "success": True, 
            "result": {"log_ref": f"mock-{endpoint_name}-ref-12345"}
        })
    
    # Generic success fallback for any other tool
    return JSONResponse(status_code=200, content={
        "success": True,
        "result": {
            "mocked": True,
            "endpoint": endpoint_name,
            "message": "Mock proxy success response"
        }
    })
