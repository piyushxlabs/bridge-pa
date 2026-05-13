import structlog
import re
import logging

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    logger_factory=structlog.PrintLoggerFactory()
)

logger = structlog.get_logger()

def filter_sensitive_data(text: str) -> str:
    """Masks common credential patterns and basic PHI from log strings."""
    if not isinstance(text, str):
        return text
    
    # Mask credentials (Bearer tokens, API keys, passwords)
    text = re.sub(r'(?i)(bearer|token|key|password|secret)[\s:=]+[\"\'\s]*[a-zA-Z0-9_\-\.]+[\"\']?', r'\1: [REDACTED]', text)
    
    # Mask basic PHI patterns (SSN)
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[PHI_REDACTED]', text)
    
    # Mask Email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b', '[PHI_REDACTED]', text)
    
    return text

def log_event(case_id: str, session_id: str, agent: str, event_type: str, description: str, audit_log_ref: str = None):
    """Logs an event as structured JSON after filtering sensitive data."""
    safe_description = filter_sensitive_data(description)
    log_kwargs = {
        "case_id": case_id,
        "session_id": session_id,
        "agent": agent,
        "event_type": event_type,
        "description": safe_description,
    }
    if audit_log_ref:
        log_kwargs["audit_log_ref"] = audit_log_ref
        
    logger.info("agent_event", **log_kwargs)
