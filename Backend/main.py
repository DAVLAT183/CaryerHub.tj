import logging
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
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

from rate_limit import RateLimitMiddleware

app.add_middleware(
    RateLimitMiddleware,
    limit=settings.RATE_LIMIT,
    window=settings.RATE_LIMIT_WINDOW,
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


@app.websocket("/ws/notifications/")
async def websocket_notifications(websocket: WebSocket, token: str = ""):
    from auth import decode_token
    from database import async_session_factory
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

    await ws_manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
