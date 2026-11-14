"""The one error shape for every route: `{ error: { code, message } }` (AD-14).

A blocked action is not an error: it returns 200 with the Decision (D5).
"""

from __future__ import annotations

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from dxp.api.models import ErrorResponse


class ApiError(Exception):
    """Raise from any route to answer with the error shape."""

    def __init__(self, status_code: int, code: str, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def not_implemented(route: str, owner: str) -> ApiError:
    """The 501 every stub route returns until its owner's PR finishes it."""
    return ApiError(501, "not_implemented", f"{route} is not implemented yet ({owner}).")


def error_body(code: str, message: str) -> dict:
    return {"error": {"code": code, "message": message}}


_STATUS_CODES = {
    400: "bad_request",
    401: "unauthorised",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    422: "invalid_request",
    429: "too_many_requests",
    500: "internal_error",
    501: "not_implemented",
    503: "unavailable",
}


def code_for_status(status_code: int) -> str:
    return _STATUS_CODES.get(status_code, "error")


async def _api_error(_: Request, exc: ApiError) -> JSONResponse:
    return JSONResponse(error_body(exc.code, exc.message), status_code=exc.status_code)


async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "Request failed."
    return JSONResponse(
        error_body(code_for_status(exc.status_code), message),
        status_code=exc.status_code,
        headers=getattr(exc, "headers", None),
    )


async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    parts = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err.get("loc", ()) if p != "body")
        parts.append(f"{loc}: {err.get('msg', 'invalid')}" if loc else err.get("msg", "invalid"))
    return JSONResponse(error_body("invalid_request", "; ".join(parts) or "Invalid request."), status_code=422)


async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
    # Never echo exception text: it could carry a key or a URL (AD-20).
    return JSONResponse(error_body("internal_error", "Internal error."), status_code=500)


def install_error_handlers(app) -> None:
    app.add_exception_handler(ApiError, _api_error)
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(Exception, _unhandled)


# Every route documents the error shape for these statuses.
ERROR_RESPONSES = {
    status: {"model": ErrorResponse, "description": code_for_status(status)}
    for status in (400, 401, 403, 404, 409, 422, 501)
}
