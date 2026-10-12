"""FastAPI application entrypoint — port of server/src/index.ts."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from api.app.config import settings
from api.app.db.database import close_db, get_db, now_iso
from api.app.db.schema import run_migrations
from api.app.errors import AppError
from api.app.lib.quota import set_quota_limit
from api.app.lib.js_json import JsJSONResponse
from api.app.logger import debug as log_debug
from api.app.logger import error as log_error
from api.app.logger import info as log_info
from api.app.logger import warn as log_warn
from api.app.routers import campaigns, clips, collections, export, quota, search, summaries
from api.app.services.whop.sync import start_periodic_whop_sync


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB and run migrations
    conn = get_db()
    run_migrations(conn)

    # Set quota limit from config
    set_quota_limit(settings.youtube_daily_quota_limit)

    # Periodic and startup sync from Whop MCP
    if settings.whop_sync_enabled:
        start_periodic_whop_sync()

    log_info(f"Server running on http://localhost:{settings.port}", {"env": settings.node_env})

    yield

    log_info("Shutting down...")
    close_db()


app = FastAPI(lifespan=lifespan, default_response_class=JsJSONResponse)

# ─── Middleware ───────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    log_debug(f"{request.method} {request.url.path}")
    return await call_next(request)


@app.middleware("http")
async def normalize_trailing_slash(request: Request, call_next):
    # Express uses non-strict routing: `/api/x/` and `/api/x` both match with no
    # redirect. Starlette/FastAPI would 307-redirect to the slashless path, so we
    # strip a single trailing slash before routing to preserve the TS contract.
    path = request.scope.get("path", "")
    if len(path) > 1 and path.endswith("/"):
        request.scope["path"] = path.rstrip("/") or "/"
    return await call_next(request)


# ─── Routes ──────────────────────────────────────────────

app.include_router(search.router, prefix="/api/search")
app.include_router(summaries.router, prefix="/api/summaries")
app.include_router(collections.router, prefix="/api/collections")
app.include_router(export.router, prefix="/api/export")
app.include_router(quota.router, prefix="/api/quota")
app.include_router(campaigns.router, prefix="/api/campaigns")
app.include_router(clips.router, prefix="/api/clips")


@app.get("/api/health")
def health():
    return {"status": "ok", "timestamp": now_iso()}


# ─── Error Handler ───────────────────────────────────────


@app.exception_handler(AppError)
async def app_error_handler(_request: Request, exc: AppError):
    log_warn(f"AppError: {exc.code}", {"message": exc.message, "status": exc.status_code})
    return JsJSONResponse(status_code=exc.status_code, content={"code": exc.code, "message": exc.message})


@app.exception_handler(RequestValidationError)
async def request_validation_handler(_request: Request, exc: RequestValidationError):
    # With every body parsed via `body: Any`, FastAPI only raises this for a
    # malformed JSON payload. TS uses express.json({strict:true}), which turns a
    # JSON parse failure (or a bare top-level scalar) into a 500 INTERNAL_ERROR,
    # so we mirror the status + envelope rather than leaking FastAPI's `{detail}`.
    message = "Unexpected token in JSON"
    for error in exc.errors():
        ctx = error.get("ctx") or {}
        if error.get("type") == "json_invalid" and ctx.get("error"):
            message = str(ctx["error"])
            break
    log_error("Request validation error", {"message": message})
    return JsJSONResponse(status_code=500, content={"code": "INTERNAL_ERROR", "message": message})


@app.exception_handler(Exception)
async def unhandled_error_handler(_request: Request, exc: Exception):
    message = str(exc) if str(exc) else "Terjadi kesalahan yang tidak diketahui"
    log_error("Unhandled error", {"error": message})
    return JsJSONResponse(status_code=500, content={"code": "INTERNAL_ERROR", "message": message})
