from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.db import Base, engine
# Импорт моделей обязателен до create_all — иначе таблицы не зарегистрируются в metadata
from app.modules.catalog import models as catalog_models  # noqa: F401
from app.modules.catalog.router import router as catalog_router
from app.modules.favorites import models as favorites_models  # noqa: F401
from app.modules.favorites.router import router as favorites_router
from app.modules.users import models as users_models  # noqa: F401
from app.modules.users.router import router as users_router
from app.modules.admin.router import router as admin_router


def create_app() -> FastAPI:
    app = FastAPI(title="UniScout API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if settings.env == "dev":
        # В dev — create_all для мгновенного старта; в проде — alembic upgrade head
        Base.metadata.create_all(engine)

    api = "/api/v1"
    app.include_router(catalog_router, prefix=api)
    app.include_router(users_router, prefix=api)
    app.include_router(favorites_router, prefix=api)
    app.include_router(admin_router, prefix=api)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
