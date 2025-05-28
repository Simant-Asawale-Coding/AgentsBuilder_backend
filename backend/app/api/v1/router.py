from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.auth import auth_api
import uvicorn

router = APIRouter()

# Include the agents/auth API
router.include_router(auth_api.router, prefix="/agentsbuilder/auth", tags=["auth"])

app = FastAPI()

# Add CORS middleware to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

@app.get("/api/v1/healthz", tags=["health"])
def health_check():
    return {"status": "ok", "service": "agentsbuilder"}

if __name__ == "__main__":
    uvicorn.run("app.api.v1.router:app", host="0.0.0.0", port=9000, reload=True)
