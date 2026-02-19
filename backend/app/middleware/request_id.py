import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Attaches a short unique ID to every request.

    - Stored on request.state.request_id so handlers and the global exception
      handler can reference it in log lines.
    - Echoed back to the caller in the X-Request-ID response header so
      clients can correlate logs with responses.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
