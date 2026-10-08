export class ModelRouterError extends Error {
  public status?: number;
  public responseBody?: any;

  constructor(message: string, status?: number, responseBody?: any) {
    super(message);
    this.name = 'ModelRouterError';
    this.status = status;
    this.responseBody = responseBody;
    Object.setPrototypeOf(this, new.target.prototype);
  }
}

export class AuthenticationError extends ModelRouterError {
  constructor(message: string, status = 401, responseBody?: any) {
    super(message, status, responseBody);
    this.name = 'AuthenticationError';
  }
}

export class RateLimitError extends ModelRouterError {
  constructor(message: string, status = 429, responseBody?: any) {
    super(message, status, responseBody);
    this.name = 'RateLimitError';
  }
}

export class APIConnectionError extends ModelRouterError {
  constructor(message: string) {
    super(message, 0);
    this.name = 'APIConnectionError';
  }
}

export class APIStatusError extends ModelRouterError {
  constructor(message: string, status: number, responseBody?: any) {
    super(message, status, responseBody);
    this.name = 'APIStatusError';
  }
}
