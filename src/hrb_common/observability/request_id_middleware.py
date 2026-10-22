"""Phase 17 - the "zero additional code beyond calling the provided
middleware" piece of the NFR spec's own acceptance criterion. The first
custom BaseHTTPMiddleware anywhere in this ecosystem - every existing
middleware (hrb_chatbot_service's CORS, hrb_api_gateway_service's
configure_cors()) uses FastAPI's own built-in CORSMiddleware, not a
hand-written one.

Imported from this submodule directly (not re-exported from
observability/__init__.py) - starlette isn't a declared dependency of the
observability extra itself, deliberately, matching the NFR spec's own "a
service with no DB access still gets retry/circuit-breaker/logging for
free" constraint: a non-web consumer (a background worker, say) shouldn't
need starlette importable just to use get_logger()/with_retry()/
CircuitBreaker()/read_secret(). Any real consumer of THIS module is a
FastAPI service by definition (you can't add FastAPI middleware without
FastAPI), so starlette is already there as that service's own dependency."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from hrb_common.observability.request_context import new_request_id, set_request_id

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIdMiddleware(BaseHTTPMiddleware):
    """A consuming service adds this with one line: app.add_middleware(RequestIdMiddleware).
    Reads an incoming X-Request-ID if the caller (or an upstream Gateway) already set one, so an
    id can propagate across service hops instead of getting a new one at every hop; generates a
    fresh one otherwise. Echoes it back on the response so a client can correlate its own call
    with server-side logs without parsing them."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or new_request_id()
        set_request_id(request_id)

        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
