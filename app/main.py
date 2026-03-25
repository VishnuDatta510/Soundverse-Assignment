import logging
import app.database as db_module
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.exc import OperationalError
from starlette_exporter import PrometheusMiddleware, handle_metrics

from app.core.config import settings
from app.models import Base
from app.routers import play
from app.services.clips import seed_clips

logger = logging.getLogger("uvicorn.error")


def _postgres_unreachable_message(exc: OperationalError) -> str:
    if exc.orig is not None:
        return str(exc.orig)
    return str(exc)


def _should_fallback_to_sqlite(exc: OperationalError) -> bool:
    if not settings.auto_sqlite_fallback:
        return False
    if settings.force_sqlite_local:
        return False
    if settings.database_url.startswith("sqlite"):
        return False
    msg = _postgres_unreachable_message(exc).lower()
    needles = (
        "could not translate host name",
        "name or service not known",
        "nodename nor servname",
        "temporary failure in name resolution",
        "network is unreachable",
        "connection timed out",
        "could not connect to server",
        "no route to host",
    )
    return any(n in msg for n in needles)


def _bootstrap_schema_and_seed():
    Base.metadata.create_all(bind=db_module.engine)
    db = db_module.SessionLocal()
    try:
        seed_clips(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        _bootstrap_schema_and_seed()
    except OperationalError as e:
        if _should_fallback_to_sqlite(e):
            logger.warning(
                "PostgreSQL/Supabase unreachable (%s). "
                "Falling back to local SQLite: %s",
                _postgres_unreachable_message(e)[:200],
                db_module.LOCAL_SQLITE_URL,
            )
            db_module.init_db(db_module.LOCAL_SQLITE_URL)
            _bootstrap_schema_and_seed()
        else:
            logger.error(
                "Database connection failed: %s. "
                "Check DATABASE_URL — on Render use Supabase pooler URL (port 6543, IPv4). "
                "If local DNS fails, set FORCE_SQLITE_LOCAL=1.",
                e,
            )
            raise

    yield


app = FastAPI(
    title=settings.app_name,
    description=(
        "A lightweight audio-preview library. "
        "All /play routes require an X-API-Key header."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    PrometheusMiddleware,
    app_name="soundverse",
    group_paths=True,
    filter_unhandled_paths=True,
)

app.add_route("/metrics", handle_metrics)

app.include_router(play.router)


@app.get("/", tags=["health"])
def root():
    return {"service": settings.app_name, "status": "ok"}
