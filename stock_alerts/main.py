from __future__ import annotations

from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .config import load_settings
from .scanner import MomentumScanner

settings = load_settings()
scanner = MomentumScanner(settings)
scheduler = BackgroundScheduler(timezone="America/New_York")

app = FastAPI(title="Momentum Scanner")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class WatchRequest(BaseModel):
    symbol: str
    note: str = ""


@app.on_event("startup")
def startup() -> None:
    scheduler.add_job(scanner.run_scan, "interval", minutes=settings.scheduler_minutes, kwargs={"force": False})
    scheduler.start()
    scanner.run_scan(force=True)


@app.on_event("shutdown")
def shutdown() -> None:
    scheduler.shutdown(wait=False)


@app.get("/api/latest")
def get_latest() -> list[dict]:
    return scanner.latest()


@app.get("/api/watchlist")
def get_watchlist() -> list[dict]:
    return [w.__dict__ for w in scanner.get_watchlist()]


@app.post("/api/watchlist/add")
def add_watch(item: WatchRequest) -> list[dict]:
    return [w.__dict__ for w in scanner.add_watch(item.symbol, item.note)]


@app.post("/api/watchlist/remove")
def remove_watch(item: WatchRequest) -> list[dict]:
    return [w.__dict__ for w in scanner.remove_watch(item.symbol)]


@app.post("/api/scan")
def trigger_scan() -> list[dict]:
    return scanner.run_scan(force=True)


static_dir = Path(__file__).resolve().parent.parent / "docs"
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="docs")
