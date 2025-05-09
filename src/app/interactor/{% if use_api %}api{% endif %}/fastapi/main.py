import os

import sentry_sdk

from hexrepo_log import LogMiddleware, setup_logger
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .api_versions.api_v1.api import api_router_v1
from app.config import config

ENVIRONMENT = os.environ.get("ENVIRONMENT", "")

setup_logger()

root_prefix = f""

if config.SENTRY_DSN:
    sentry_sdk.init(
        dsn=config.SENTRY_DSN,
        # Add data like request headers and IP for users,
        # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
        send_default_pii=True,
    )

app = FastAPI(
    title="{{project_slug}} Service",
    description="{{project_slug}} description",
    version="1.0.0",
    root_path=root_prefix,
)

app.add_middleware(LogMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
# Sets all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SessionMiddleware, secret_key=config.SESSION_SECRET, max_age=None)
app.include_router(api_router_v1, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "{{project_slug}} service"}
