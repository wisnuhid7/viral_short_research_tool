/** Structured API error for consistent error responses */
export class AppError extends Error {
  constructor(
    public readonly code: string,
    message: string,
    public readonly statusCode: number = 500,
  ) {
    super(message);
    this.name = 'AppError';
  }
}

export class NotFoundError extends AppError {
  constructor(message: string) {
    super('NOT_FOUND', message, 404);
  }
}

export class ValidationError extends AppError {
  constructor(message: string) {
    super('VALIDATION_ERROR', message, 400);
  }
}

export class QuotaExceededError extends AppError {
  constructor(message: string = 'Kuota YouTube API harian telah habis. Coba lagi besok.') {
    super('QUOTA_EXCEEDED', message, 429);
  }
}

export class ExternalApiError extends AppError {
  constructor(service: string, message: string) {
    super('EXTERNAL_API_ERROR', `${service}: ${message}`, 502);
  }
}
