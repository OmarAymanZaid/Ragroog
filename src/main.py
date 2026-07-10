import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from loguru import logger

from helpers.config import get_settings
from utils.logging import configure_logging


settings = get_settings()

# ==========================================
# THE APPLICATION LIFESPAN
# ==========================================
@asynccontextmanager
async def application_lifespan(app: FastAPI) -> AsyncIterator[None]:
    
    configure_logging(level=settings.LOG_LEVEL)
    logger.info(f"Starting {settings.APP_NAME} in [{settings.ENVIRONMENT}] mode...")
    
    # Reusable global resources attach to app instance here
    # (e.g., app.db_client = DatabaseClient())
    logger.info("Application infrastructure initialized successfully.")
    
    yield
    
    logger.info("Initiating application shutdown sequence...")
    # 3. Graceful resource cleanup execution goes here
    # (e.g., await app.db_client.disconnect())
    logger.info("Application safely stopped. Goodbye!")



# ==========================================
# THE APPLICATION FACTORY
# ==========================================
def create_app() -> FastAPI:
    """Configures and builds the primary FastAPI application instance."""
    
    # 1. Instantiate the app using dynamic config properties
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=application_lifespan,
    )

    # ------------------- 
    # Routes & endpoints
    # -------------------


    @app.get("/", status_code=200, include_in_schema=False)
    async def root_ping() -> dict[str, str]:
        """Simple application heartbeat ping response."""
        return {"service": app.title, "status": "online", "version": app.version}

    @app.get("/healthz", status_code=200, tags=["Infrastructure"])
    async def system_health_check() -> dict[str, str]:
        """Liveness/readiness probe context for monitoring stacks."""
        return {"status": "healthy"}

    return app


app = create_app()