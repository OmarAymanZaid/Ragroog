import sys
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from loguru import logger

from pymongo import AsyncMongoClient

from helpers.config import get_settings
from utils.logging import configure_logging

from routes import data


settings = get_settings()

# ==========================================
# THE APPLICATION LIFESPAN
# ==========================================
@asynccontextmanager
async def application_lifespan(app: FastAPI) -> AsyncIterator[None]:
    
    configure_logging(level=settings.LOG_LEVEL)
    logger.info(f"Starting {settings.APP_NAME} in [{settings.ENVIRONMENT}] mode...")
    
    # ------------------------------------------------------
    # Reusable global resources attach to app instance here
    # ------------------------------------------------------

    # 1. Database Engine & Session initialization
    logger.info("Connecting to MongoDB cluster asynchronously...")
    app.mongo_client = AsyncMongoClient(settings.MONGODB_URL)
    app.db = app.mongo_client[settings.MONGODB_DATABASE]

    try:
        await app.db.command("ping")
        logger.info(f"Successfully connected to MongoDB database: [{settings.MONGODB_DATABASE}]")
    except Exception as exc:
        logger.critical(f"Failed to communicate with MongoDB instance: {exc}")
        raise exc


    logger.info("Application infrastructure initialized successfully.")
    
    yield
        
    # ------------------------------------------------------
    #  Graceful resource cleanup execution goes here
    # ------------------------------------------------------
    logger.info("Initiating application shutdown sequence...")

    # 1. Close database connections
    logger.info("Initiating MongoDB connection shutdown sequence...")
    app.mongo_client.close()
    logger.info("MongoDB connection pool safely dropped.")
    
    
    logger.info("Application safely stopped.")



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
    app.include_router(data.data_router)


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