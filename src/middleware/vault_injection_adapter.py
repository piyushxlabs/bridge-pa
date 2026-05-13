import os
import httpx
from src.utils.logger import log_event

_credential_context: dict[str, any] = {}

SECRET_VAULT_ENDPOINT = os.getenv("SECRET_VAULT_ENDPOINT", "http://localhost:8080/vault")
SECRET_VAULT_AUTH_TOKEN = os.getenv("SECRET_VAULT_AUTH_TOKEN", "mock-token")

async def inject_vault_credentials(session_id: str, target_agent: str) -> bool:
    """Fetches credentials from the secret vault and injects them into the local context."""
    headers = {"Authorization": f"Bearer {SECRET_VAULT_AUTH_TOKEN}"}
    payload = {"session_id": session_id, "target_agent": target_agent}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(SECRET_VAULT_ENDPOINT, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            if "credentials" in data:
                _credential_context[session_id] = data["credentials"]
                return True
            return False
    except Exception as e:
        log_event(
            case_id="SYSTEM",
            session_id=session_id,
            agent="vault_injection_adapter",
            event_type="vault_injection_failed",
            description=f"Failed to inject credentials for {target_agent}"
        )
        return False

def get_injected_credentials(session_id: str) -> dict | None:
    return _credential_context.get(session_id)

def clear_credentials(session_id: str):
    if session_id in _credential_context:
        del _credential_context[session_id]
