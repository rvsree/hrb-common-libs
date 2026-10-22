from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from hrb_common.observability.request_context import get_request_id
from hrb_common.observability.request_id_middleware import REQUEST_ID_HEADER, RequestIdMiddleware


async def _echo_request_id(request):
    return JSONResponse({"seen_inside_handler": get_request_id()})


def _build_app() -> Starlette:
    app = Starlette(routes=[Route("/echo", _echo_request_id)])
    app.add_middleware(RequestIdMiddleware)
    return app


def test_generates_request_id_when_header_missing():
    client = TestClient(_build_app())

    response = client.get("/echo")

    generated_id = response.headers[REQUEST_ID_HEADER]
    assert generated_id
    assert response.json()["seen_inside_handler"] == generated_id


def test_propagates_incoming_request_id_unchanged():
    client = TestClient(_build_app())

    response = client.get("/echo", headers={REQUEST_ID_HEADER: "caller-supplied-id"})

    assert response.headers[REQUEST_ID_HEADER] == "caller-supplied-id"
    assert response.json()["seen_inside_handler"] == "caller-supplied-id"
