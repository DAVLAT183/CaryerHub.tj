import logging
import json
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from config import settings
from database import init_db
from scheduler import setup_scheduler

BASE_DIR = Path(__file__).resolve().parent
MEDIA_DIR = BASE_DIR / "media"
MEDIA_DIR.mkdir(exist_ok=True)
(MEDIA_DIR / "avatars").mkdir(exist_ok=True)

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


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


from rate_limit import RateLimitMiddleware

app.add_middleware(
    RateLimitMiddleware,
    limit=settings.RATE_LIMIT,
    window=settings.RATE_LIMIT_WINDOW,
)

# CORS must be added last so it is the outermost middleware
# and wraps rate-limit 429s / exception responses too.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from routes_auth import router as auth_router
from routes_parser import router as parser_router
from routes_jobs import router as jobs_router
from routes_extras import extras_router
from routes_payments import payments_router
from routes_users import router as users_router
from routes_misc import router as misc_router
from routes_ai import router as ai_router

app.include_router(auth_router, prefix="/api")
app.include_router(parser_router, prefix="/api")
app.include_router(jobs_router)
app.include_router(extras_router)
app.include_router(payments_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(misc_router)
app.include_router(ai_router, prefix="/api")

app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")


@app.get("/")
async def root():
    return {"message": "CareerHub API is running", "docs": "/docs"}


@app.get("/api/")
async def api_root():
    return {"message": "CareerHub API v1"}


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: int):
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: int):
        if user_id in self.active_connections:
            self.active_connections[user_id] = [
                ws for ws in self.active_connections[user_id] if ws != websocket
            ]
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_to_user(self, user_id: int, data: dict):
        if user_id in self.active_connections:
            for ws in self.active_connections[user_id]:
                try:
                    await ws.send_json(data)
                except Exception:
                    pass


ws_manager = ConnectionManager()
app.state.ws_manager = ws_manager


@app.websocket("/ws/notifications/")
async def websocket_notifications(websocket: WebSocket, token: str = ""):
    from auth import decode_token
    from database import async_session
    from models import User
    from sqlalchemy import select

    if not token:
        await websocket.close(code=4001)
        return

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        await websocket.close(code=4001)
        return

    user_id = int(payload.get("sub", 0))
    if not user_id:
        await websocket.close(code=4001)
        return

    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        db_user = result.scalar_one_or_none()

    if not db_user or not db_user.is_active or not db_user.is_email_verified:
        await websocket.close(code=4003)
        return

    await ws_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
