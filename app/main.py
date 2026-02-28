"""
SAIA Insurance Broker Platform - Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys

from app.config import settings
from app.api import chat, whatsapp, auth

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="منصة SAIA لوساطة التأمين - شركة كونكر | Powered by Bineyes",
    docs_url="/docs",
    redoc_url="/redoc"
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix=settings.API_PREFIX, tags=["Chat"])
app.include_router(whatsapp.router, prefix=settings.API_PREFIX, tags=["WhatsApp"])
app.include_router(auth.router, prefix=settings.API_PREFIX, tags=["Auth"])


@app.on_event("startup")
async def startup():
    """Application startup"""
    logger.info("=" * 50)
    logger.info(f"🚀 {settings.API_TITLE} v{settings.API_VERSION} starting...")
    
    # Initialize MongoDB
    try:
        from app.db.mongodb import mongodb_manager
        await mongodb_manager.connect()
        logger.info("✅ MongoDB connected successfully")
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")

    # Initialize SQL Engine
    try:
        from app.engine.sql_engine import insurance_sql_engine
        logger.info("✅ SQL Database Engine initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize SQL Engine: {e}")

    # Initialize Users Table
    try:
        from app.db.users import user_repository
        await user_repository.init_table()
        logger.info("✅ Users table initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Users table: {e}")

    logger.info(f"📍 API Prefix: {settings.API_PREFIX}")
    logger.info(f"🔧 Debug: {settings.DEBUG}")
    logger.info("=" * 50)


@app.on_event("shutdown")
async def shutdown():
    """Application shutdown"""
    logger.info("👋 Shutting down SAIA Platform...")


@app.get("/", tags=["Root"])
async def root():
    """نقطة الدخول الرئيسية"""
    return {
        "message": "مرحباً بك في SAIA - منصة كونكر لوساطة التأمين",
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "company": "شركة كونكر لوساطة التأمين",
        "powered_by": "Bineyes",
        "docs": "/docs"
    }



@app.get("/health", tags=["Health"])
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.API_TITLE,
        "version": settings.API_VERSION
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )
