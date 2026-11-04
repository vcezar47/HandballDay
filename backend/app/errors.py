"""Application errors. Raise these anywhere; the handler in main.py turns them into JSON."""

from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code = 500
    code = "app_error"

    def __init__(self, message: str = "Something went wrong") -> None:
        super().__init__(message)
        self.message = message


class AppValidationError(AppError):
    status_code = 422
    code = "validation_error"


class AuthError(AppError):
    status_code = 401
    code = "unauthenticated"


class ForbiddenError(AppError):
    status_code = 403
    code = "forbidden"


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"


class ConflictError(AppError):
    status_code = 409
    code = "conflict"


class PaymentError(AppError):
    status_code = 402
    code = "payment_failed"


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    # "detail" matches FastAPI's own error shape, so the frontend reads both the same way.
    return JSONResponse({"detail": exc.message, "code": exc.code}, status_code=exc.status_code)
