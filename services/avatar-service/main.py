from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import avatar
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="SereneMind Avatar Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(avatar.router, prefix="/avatar", tags=["Avatar"])

@app.get("/health")
async def health():
    return {"status": "ok", "service": "avatar-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
