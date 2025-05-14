from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow CORS for UI development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.services.tool_registry import get_tools as get_tools_registry
from app.services.framework_registry import get_frameworks as get_frameworks_registry, get_framework_creds_schema
from fastapi import APIRouter
from app.api import agent as agent_router
from app.api import agent_lifecycle as agent_lifecycle_router

app.include_router(agent_router.router, prefix="/api")
app.include_router(agent_lifecycle_router.router, prefix="/api")

@app.get("/tools")
def get_tools():
    return {"tools": get_tools_registry()}

@app.get("/frameworks")
def get_frameworks():
    return {"frameworks": get_frameworks_registry()}

@app.get("/creds_schema/{framework_name}")
def get_creds_schema(framework_name: str):
    return get_framework_creds_schema(framework_name)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)
