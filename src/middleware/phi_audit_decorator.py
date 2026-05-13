import functools
from src.utils.exceptions import WorkflowHaltedException

# These will be fully implemented in Step 8
from src.tools import write_phi_audit_log
from src.tools import trigger_emergency_stop

def phi_audit_required(phi_fields: list[str]):
    """
    Decorator that enforces HIPAA PHI Audit Log requirements before node execution.
    If audit log write fails, it triggers an emergency stop and halts the workflow.
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(state: dict, *args, **kwargs):
            session_id = state.get("session", {}).get("session_id", "unknown_session")
            agent_name = func.__name__ # Using function name as agent name
            
            for field in phi_fields:
                audit_params = {
                    "field_name": field,
                    "action_type": "access",
                    "agent_name": agent_name,
                    "session_id": session_id
                }
                
                result = await write_phi_audit_log.execute(audit_params)
                
                if not result.get("success", False):
                    stop_params = {
                        "scope": "case",
                        "reason": f"PHI Audit Log Write Failed for field: {field}",
                        "case_id": state.get("session", {}).get("case_id", "unknown_case")
                    }
                    await trigger_emergency_stop.execute(stop_params)
                    raise WorkflowHaltedException(f"PHI Audit Failed. Workflow halted for field {field}.")
                    
            return await func(state, *args, **kwargs)
        return wrapper
    return decorator
