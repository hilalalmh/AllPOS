from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.security import assert_secure_config
from app.core.storage import upload_dir
from app.routers import router as api_router


class _SecurityHeadersMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend(
                    [
                        (b"X-Content-Type-Options", b"nosniff"),
                        (b"X-Frame-Options", b"DENY"),
                        (b"Referrer-Policy", b"no-referrer"),
                        (
                            b"Content-Security-Policy",
                            b"default-src 'self'; img-src 'self' data:; "
                            b"style-src 'self' 'unsafe-inline'; "
                            b"script-src 'self'; connect-src 'self'",
                        ),
                        (b"X-XSS-Protection", b"1; mode=block"),
                    ]
                )
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)


def create_app() -> FastAPI:
    assert_secure_config()

    is_production = settings.ENVIRONMENT == "production"
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        docs_url=None if is_production else "/docs",
        redoc_url=None if is_production else "/redoc",
        openapi_url=None if is_production else "/openapi.json",
    )

    app.mount("/uploads", StaticFiles(directory=upload_dir()), name="uploads")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(_SecurityHeadersMiddleware)
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()