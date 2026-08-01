import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.api.routes import router
from app.core.config import get_settings
from app.database import Base, engine
from app import models
from app.services.realtime import hub

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield
app = FastAPI(title="SentinelAI API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_origins.split(","), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
@app.exception_handler(Exception)
async def unhandled(_: Request, exc: Exception):
    logging.exception("Unhandled API error", exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred"})
app.include_router(router, prefix="/api/v1", tags=["SentinelAI"])
@app.get("/health")
def health(): return {"status": "ok"}
@app.get("/api/v1/public/status")
def public_status(): return {"status":"operational","server_time":datetime.now(timezone.utc).isoformat(),"active_live_sessions":hub.active_count}
