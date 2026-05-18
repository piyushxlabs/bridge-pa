"""
Launcher for the Mock VeeaHub Edge Logging Proxy.

Usage:
  python -m src.mock_proxy.start_proxy
"""
import uvicorn
import os

if __name__ == "__main__":
    port = int(os.getenv("MOCK_PROXY_PORT", "8080"))
    host = os.getenv("MOCK_PROXY_HOST", "0.0.0.0")
    
    print("=" * 50)
    print(f"Starting VeeaHub Edge Mock Proxy on port {port}")
    print("=" * 50)
    
    uvicorn.run("src.mock_proxy.main:app", host=host, port=port, reload=True)
