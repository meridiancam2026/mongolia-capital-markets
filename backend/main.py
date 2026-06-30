import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env before any local imports that read environment variables
_project_root = Path(__file__).resolve().parents[1]
load_dotenv(_project_root / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import bonds, macro, otc, quotes, regulatory, securities

app = FastAPI(title="Mongolia Capital Markets API", version="0.1.0")

origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(securities.router, prefix="/api/securities", tags=["securities"])
app.include_router(quotes.router,     prefix="/api/quotes",     tags=["quotes"])
app.include_router(otc.router,        prefix="/api/otc",        tags=["otc"])
app.include_router(bonds.router,      prefix="/api/bonds",      tags=["bonds"])
app.include_router(macro.router,      prefix="/api/macro",      tags=["macro"])
app.include_router(regulatory.router, prefix="/api/regulatory", tags=["regulatory"])


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
