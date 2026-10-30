"""Error types and handlers that keep the legacy `{ error, message?, details? }` response shape."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from chatbot.schemas import ErrorDetail, ErrorResponse


class ApiError(Exception):
    def __init__(self, status_code: int, error: str, message: str | None = None) -> None:
        super().__init__(error)
        self.status_code = status_code
        self.error = error
        self.message = message


def _json(status_code: int, body: ErrorResponse) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=body.model_dump(mode="json", by_alias=True, exclude_none=True),
    )


async def _api_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ApiError)
    return _json(exc.status_code, ErrorResponse(error=exc.error, message=exc.message))


async def _validation_error_handler(_: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    details = [
        ErrorDetail(
            # Drop the leading "body"/"query" location, as the legacy API did.
            path=[p for p in err["loc"][1:] if isinstance(p, str | int)],
            message=err["msg"],
        )
        for err in exc.errors()
    ]
    return _json(400, ErrorResponse(error="Invalid request", details=details))


async def _unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    # TODO(observability): log the exception with a request id once tracing is added.
    return _json(
        500,
        ErrorResponse(
            error="An error occurred processing your message",
            message="Please try again later or contact support",
        ),
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApiError, _api_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_exception_handler(Exception, _unhandled_error_handler)
