from uuid import UUID

from jose import JWTError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.application.services.auth_service import AuthService

SKIP_PATHS = ("/auth/", "/health")


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path.startswith(SKIP_PATHS):
            return await call_next(request)

        request.state.tenant_id = None

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ")
            try:
                payload = await AuthService.decode_access_token(token)
                raw = payload.get("tenant_id")
                request.state.tenant_id = UUID(raw) if raw else None
            except (JWTError, ValueError):
                request.state.tenant_id = None

        return await call_next(request)
