from urllib.parse import urlsplit, urlunsplit

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings

app = FastAPI(title=settings.app_name)


def _cors_origins(frontend_url: str) -> list[str]:
    parsed = urlsplit(frontend_url)
    origins = {frontend_url}

    if parsed.hostname == "localhost":
        origins.add(
            urlunsplit(
                (
                    parsed.scheme,
                    f"127.0.0.1:{parsed.port}" if parsed.port else "127.0.0.1",
                    parsed.path,
                    "",
                    "",
                )
            )
        )
    elif parsed.hostname == "127.0.0.1":
        origins.add(
            urlunsplit(
                (
                    parsed.scheme,
                    f"localhost:{parsed.port}" if parsed.port else "localhost",
                    parsed.path,
                    "",
                    "",
                )
            )
        )

    return sorted(origins)


app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins(settings.frontend_url),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
