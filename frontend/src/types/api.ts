export interface HealthStatus {
  status: string;
  application: string;
  version: string;
  database?: string;
}

export interface StandardizedApiError {
  success: false;
  error: {
    code: string;
    message: string;
    details?: unknown;
  };
}
