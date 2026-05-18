"""
Mock VeeaHub Edge Logging Proxy (Port 8080)

This is a local development mock server that intercepts all external tool calls
made by the Bridge-PA backend. It returns successful stub responses to ensure
end-to-end local testing without triggering ConnectionRefusedError or WorkflowHaltedException.

CRITICAL: This mock must NEVER be run in a production environment.
"""
import os
import sys
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("veea-mock-proxy")

# Safety check
if os.getenv("ENVIRONMENT", "local").lower() == "production":
    logger.critical("FATAL: Attempted to start mock proxy in PRODUCTION environment. Halting.")
    sys.exit(1)

app = FastAPI(title="VeeaHub Edge Mock Proxy", version="1.0.0")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"MOCK PROXY INTERCEPT: {request.method} {request.url.path}")
    response = await call_next(request)
    return response

from src.mock_proxy.routes import router
app.include_router(router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "veea-mock-proxy"}
