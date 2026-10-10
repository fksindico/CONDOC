import type { ApiError } from '@condc/api-contracts';

let currentTenantId: string | null = localStorage.getItem('condc_active_tenant_id');

export function setApiTenantId(tenantId: string | null): void {
  currentTenantId = tenantId;
  if (tenantId) {
    localStorage.setItem('condc_active_tenant_id', tenantId);
  } else {
    localStorage.removeItem('condc_active_tenant_id');
  }
}

export function getApiTenantId(): string | null {
  return currentTenantId;
}

export class ApiClientError extends Error {
  code: string;
  status: number;
  details?: Record<string, string[]>;
  requestId?: string;

  constructor(status: number, errorData: Partial<ApiError>) {
    super(errorData.message || `Erro na requisição (${status})`);
    this.name = 'ApiClientError';
    this.status = status;
    this.code = errorData.code || 'UNKNOWN_ERROR';
    this.details = errorData.details;
    this.requestId = errorData.request_id;
  }
}

interface RequestOptions extends RequestInit {
  tenantId?: string | null;
  etag?: string | null;
}

export interface ApiResponseWithHeaders<T> {
  data: T;
  etag?: string | null;
  status: number;
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<ApiResponseWithHeaders<T>> {
  const url = endpoint.startsWith('http') ? endpoint : `/api/v1${endpoint.startsWith('/') ? '' : '/'}${endpoint}`;

  const headers = new Headers(options.headers || {});
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  headers.set('Accept', 'application/json');

  const tenant = options.tenantId !== undefined ? options.tenantId : currentTenantId;
  if (tenant) {
    headers.set('X-Tenant-ID', tenant);
  }

  if (options.etag) {
    headers.set('If-Match', options.etag);
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include', // Mandatório ADR-002: cookies HttpOnly BFF
  });

  const responseEtag = response.headers.get('ETag');

  if (!response.ok) {
    let errorJson: Partial<ApiError> = {};
    try {
      errorJson = await response.json();
    } catch {
      errorJson = { message: response.statusText };
    }
    throw new ApiClientError(response.status, errorJson);
  }

  if (response.status === 204) {
    return { data: null as unknown as T, etag: responseEtag, status: response.status };
  }

  const contentType = response.headers.get('Content-Type');
  if (contentType && contentType.includes('application/json')) {
    const data = await response.json();
    return { data, etag: responseEtag, status: response.status };
  }

  const textData = await response.text();
  return { data: textData as unknown as T, etag: responseEtag, status: response.status };
}

export const api = {
  get: <T>(endpoint: string, options?: RequestOptions) => request<T>(endpoint, { ...options, method: 'GET' }),
  post: <T>(endpoint: string, body?: unknown, options?: RequestOptions) =>
    request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),
  put: <T>(endpoint: string, body?: unknown, options?: RequestOptions) =>
    request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),
  patch: <T>(endpoint: string, body?: unknown, options?: RequestOptions) =>
    request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: body instanceof FormData ? body : JSON.stringify(body),
    }),
  delete: <T>(endpoint: string, options?: RequestOptions) => request<T>(endpoint, { ...options, method: 'DELETE' }),
};
