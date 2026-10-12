"""Structured API errors for consistent error responses.

Port of server/src/lib/errors.ts.
"""


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 500):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class NotFoundError(AppError):
    def __init__(self, message: str):
        super().__init__("NOT_FOUND", message, 404)


class ValidationError(AppError):
    def __init__(self, message: str):
        super().__init__("VALIDATION_ERROR", message, 400)


class QuotaExceededError(AppError):
    def __init__(self, message: str = "Kuota YouTube API harian telah habis. Coba lagi besok."):
        super().__init__("QUOTA_EXCEEDED", message, 429)


class ExternalApiError(AppError):
    def __init__(self, service: str, message: str):
        super().__init__("EXTERNAL_API_ERROR", f"{service}: {message}", 502)