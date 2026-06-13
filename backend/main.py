import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import SEED_DEMO, cors_origins
import database as db
from routes_attachments import router as attachments_router
from routes_auth import router as auth_router
from routes_kb import router as kb_router
from routes_metrics import router as metrics_router
from routes_password import router as password_router
from routes_tickets import router as tickets_router
from seed import seed_demo


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    if SEED_DEMO:
        seed_demo()
    yield


app = FastAPI(title="pato.do.problema API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins(),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(tickets_router)
app.include_router(attachments_router)
app.include_router(metrics_router)
app.include_router(password_router)
app.include_router(kb_router)

_front = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(_front):
    app.mount("/", StaticFiles(directory=_front, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
