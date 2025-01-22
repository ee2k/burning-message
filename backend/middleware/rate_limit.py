from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime, timedelta
from collections import defaultdict
from utils.error_codes import CommonErrorCodes, STATUS_CODES
from constants import CONTENT_TYPE, APPLICATION_JSON, detail
import logging
import os
from dotenv import load_dotenv
from starlette.responses import JSONResponse

# Load environment variables
load_dotenv()

# Configure logger
logger = logging.getLogger("rate_limiter")
# Get log level from environment
log_level = os.getenv("LOG_LEVEL", "info").upper()
logger.setLevel(getattr(logging, log_level))

class RateLimiter(BaseHTTPMiddleware):
    def __init__(self, app, limits: dict = None):
        super().__init__(app)
        self.limits = limits or {
            "/message/create": {"ip_limit": 10, "window_size": 60},
            "/chat/": {"ip_limit": 20, "window_size": 60}
        }
        self.ip_requests = defaultdict(lambda: defaultdict(list))
        logger.info(f"RateLimiter initialized with limits: {self.limits}")
    
    async def dispatch(self, request: Request, call_next):
        try:
            client_ip = request.client.host
            path = request.url.path
            now = datetime.now()

            # Find matching rate limit configuration
            limit_config = next(
                (config for route, config in self.limits.items() if path.startswith(route)),
                None
            )

            if limit_config:
                window_size = limit_config["window_size"]
                ip_limit = limit_config["ip_limit"]
                minute_ago = now - timedelta(seconds=window_size)

                # Clean old requests
                self.ip_requests[client_ip][path] = [
                    ts for ts in self.ip_requests[client_ip][path] 
                    if ts > minute_ago
                ]

                # Check IP limit
                if len(self.ip_requests[client_ip][path]) >= ip_limit:
                    # oldest = self.ip_requests[client_ip][path][0]
                    # wait_time = (oldest + timedelta(seconds=window_size) - now).seconds
                    logger.warning(f"Rate limit exceeded for IP {client_ip} on {path}")
                    return JSONResponse(
                        status_code=STATUS_CODES[CommonErrorCodes.TOO_MANY_REQUESTS],
                        content={detail: "Too many requests"},
                        headers={CONTENT_TYPE: APPLICATION_JSON}
                    )

                # Add new request
                self.ip_requests[client_ip][path].append(now)

            return await call_next(request)
        except Exception as e:
            logger.error(f"Error in rate limiter: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=STATUS_CODES[CommonErrorCodes.SERVER_ERROR],
                detail="Internal server error"
            ) 