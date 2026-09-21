import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from database import init_db
from scheduler import setup_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("careerhub")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    await init_db()
    logger.info("Setting up scheduler...")
    setup_scheduler()
    logger.info("CareerHub API started!")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routes_auth import router as auth_router
from routes_main import router as main_router
from routes_parser import router as parser_router
from routes_jobs import router as jobs_router

app.include_router(auth_router, prefix="/api")
app.include_router(main_router, prefix="/api")
app.include_router(parser_router, prefix="/api")
app.include_router(jobs_router)


@app.get("/")
async def root():
    return {"message": "CareerHub API is running", "docs": "/docs"}


@app.get("/api/")
async def api_root():
    return {"message": "CareerHub API v1"}
