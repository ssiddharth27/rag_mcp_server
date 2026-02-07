import os
import requests
from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from usage_store import check_rate_limit, get_usage_stats

mcp = FastMCP("Authenticated RAG MCP Server")

VALID_KEYS = os.getenv("MCP_API_KEYS", "").split(",")
ADMIN_KEY = os.getenv("ADMIN_KEY")


def verify_key(api_key: str):
    if api_key not in VALID_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
@mcp.tool()
def ask_rag(query: str, api_key: str) -> str:
    verify_key(x_api_key)
    if not check_rate_limit(api_key):
        return "Rate limit exceeded (5 requests/min). Try again letter"
    try: 
        res = request.post(
            "http://localhost:8000/rag",
            json={"query": query},
            timeout=60
        )
        return res.json()["answer"]
    except Exception as e:
        return f"Server error: {str(e)}"
    
    answer = qa_chain.run(query.question)
    return {"answer": answer}

@mcp.tool()
def usage_stats(admin_key: str) -> str:
    if admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Not authorized")
    return str(get_usage_stats())

if __name__ == "main":
    mcp.run(transport="http", host="0.0.0.0", port=7860)
