from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from routes.api import api_router
from fastapi.responses import JSONResponse
from pathlib import Path
from middleware.message_rate_limit import MessageRateLimiter
from middleware.chat_rate_limit import ChatRateLimiter
import logging
from contextlib import asynccontextmanager
from datetime import datetime
import os
from typing import List
from fastapi import HTTPException
import sys
import signal
import traceback
from dotenv import load_dotenv
from middleware.security_headers import SecurityHeadersMiddleware
from middleware.unmatched_request_limiter import UnmatchedRequestLimiter
from routes.chat.websocket import router as websocket_router
import asyncio
from routes.chat.websocket import WebSocketManager

# Load environment variables from .env file
load_dotenv()

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = PROJECT_ROOT / "logs"

# Create logs directory if it doesn't exist
LOG_DIR.mkdir(exist_ok=True)

# Configure logging
log_level = os.getenv("LOG_LEVEL", "info").upper()

logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "app.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

websocket_manager = WebSocketManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    logger.info(f"Application starting up with log level ===: {log_level}")
    try:
        # Startup: Initialize resources
        from services.message_store import MessageStore
        await MessageStore().initialize()
        logger.info("Application startup complete")
        asyncio.create_task(websocket_manager.check_connections())
        yield
    finally:
        # Shutdown: Cleanup resources
        logger.info("Application shutting down...")
        try:
            from services.message_store import MessageStore
            await MessageStore().cleanup()
            logger.info("Application shutdown complete")
        except Exception as e:
            logger.error(f"Shutdown error: {e}", exc_info=True)

# Production settings
app = FastAPI(
    title="Burn after reading message",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan
)

# Get CORS origins from environment variable
def get_cors_origins() -> List[str]:
    origins = os.getenv("CORS_ORIGINS", "http://localhost")
    return [origin.strip() for origin in origins.split(",")]

# always put RateLimiter before CORSMiddleware and routers
app.add_middleware(
    MessageRateLimiter,
    limits={
        "/message/create": {"ip_limit": 6, "window_size": 60}
    }
)

app.add_middleware(
    ChatRateLimiter
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add security middlewares
app.add_middleware(SecurityHeadersMiddleware)

# Include routers
# app.include_router(pages_router)
app.include_router(api_router, prefix="/api")
app.include_router(websocket_router, prefix="/ws")

# Error handling - Order matters!
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.info(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(
        f"Uncaught exception\n"
        f"Path: {request.url.path}\n"
        f"Method: {request.method}\n"
        f"Error: {str(exc)}\n"
        f"Traceback: {traceback.format_exc()}"
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Add any specific health checks here
        # Example: Check message store
        from services.message_store import MessageStore
        store_status = await MessageStore().check_health()
        
        return {
            "status": "healthy",
            "message_store": store_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = datetime.now()
    try:
        response = await call_next(request)
        duration = datetime.now() - start_time
        logger.info(
            f"Path: {request.url.path} "
            f"Method: {request.method} "
            f"Duration: {duration.total_seconds():.3f}s "
            f"Status: {response.status_code}"
        )
        return response
    except Exception as e:
        logger.error(
            f"Request failed - Path: {request.url.path} "
            f"Method: {request.method} "
            f"Error: {str(e)}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        raise

# Signal handlers
def signal_handler(signum, frame):
    sig_name = signal.Signals(signum).name
    logger.info(f"Received signal {sig_name} ({signum})")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

app.add_middleware(UnmatchedRequestLimiter)

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Get configuration from environment variables
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"Starting server - Host: {host}, Port: {port}")
    
    # Don't run with these settings directly
    # Use external uvicorn command instead
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*",
        log_level=log_level
    )