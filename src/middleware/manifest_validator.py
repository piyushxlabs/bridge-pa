import json
import os
from src.utils.logger import log_event

MANIFEST_PATH = os.path.join(os.path.dirname(__file__), '..', 'config', 'integration_manifest_v1.0.0.json')

def load_manifest():
    with open(MANIFEST_PATH, 'r') as f:
        return json.load(f)

def validate_endpoint(endpoint_id: str, manifest_version: str) -> bool:
    manifest = load_manifest()
    
    if manifest_version not in manifest:
        log_event(
            case_id="SYSTEM",
            session_id="SYSTEM",
            agent="manifest_validator",
            event_type="prohibited_action",
            description=f"Manifest version {manifest_version} not found"
        )
        return False
        
    approved_endpoints = manifest[manifest_version]
    if endpoint_id in approved_endpoints:
        return True
    else:
        log_event(
            case_id="SYSTEM",
            session_id="SYSTEM",
            agent="manifest_validator",
            event_type="prohibited_action",
            description=f"Endpoint {endpoint_id} is not approved in manifest {manifest_version}"
        )
        return False
