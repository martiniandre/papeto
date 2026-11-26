import { tokenStorage } from './tokenStorage';
import type { ApiErrorBody, ApiErrorCode, TokenPair } from './types';

export const API_BASE_URL = (process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000').replace(
  /\/+$/,
  '',
);

/** Error codes produced by the client itself (not by the backend). */
export const NETWORK_ERROR = 'NETWORK_ERROR';
export const UNKNOWN_ERROR = 'UNKNOWN_ERROR';
export const ABORTED = 'ABORTED';

export class ApiError extends Error {
  readonly status: number;
  readonly code: ApiErrorCode;

  constructor(status: number, code: ApiErrorCode, message: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
  }
}

export const isApiError = (value: unknown): value is ApiError => value instanceof ApiError;

type Listener = () => void;
let onUnauthorized: Listener | null = null;

/** Called when the session cannot be refreshed (the app signs the user out). */
export function setUnauthorizedListener(listener: Listener | null): void {
  onUnauthorized = listener;
}

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  body?: unknown;
  query?: Record<string, string | undefined>;
  signal?: AbortSignal;
  /** Send without the Authorization header (auth endpoints). */
  anonymous?: boolean;
}

function buildUrl(path: string, query?: RequestOptions['query']): string {
  const url = `${API_BASE_URL}/v1${path}`;
  if (!query) return url;
  const params = Object.entries(query)
    .filter((entry): entry is [string, string] => entry[1] !== undefined)
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`);
  return params.length ? `${url}?${params.join('&')}` : url;
}

async function toApiError(response: Response): Promise<ApiError> {
  try {
    const body = (await response.json()) as Partial<ApiErrorBody>;
    if (body?.error?.code) {
      return new ApiError(response.status, body.error.code, body.error.message ?? '');
    }
  } catch {
    // Body is not JSON; fall through.
  }
  return new ApiError(response.status, UNKNOWN_ERROR, `HTTP ${response.status}`);
}

let refreshing: Promise<boolean> | null = null;

async function refreshTokens(): Promise<boolean> {
  const current = await tokenStorage.get();
  if (!current) return false;
  try {
    const response = await fetch(buildUrl('/auth/refresh'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ refresh_token: current.refresh_token }),
    });
    if (!response.ok) return false;
    await tokenStorage.set((await response.json()) as TokenPair);
    return true;
  } catch {
    return false;
  }
}

async function send(path: string, options: RequestOptions): Promise<Response> {
  const headers: Record<string, string> = { Accept: 'application/json' };
  let body: BodyInit | undefined;
  if (options.body instanceof FormData) {
    body = options.body;
  } else if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(options.body);
  }
  if (!options.anonymous) {
    const tokens = await tokenStorage.get();
    if (tokens) headers.Authorization = `Bearer ${tokens.access_token}`;
  }
  try {
    return await fetch(buildUrl(path, options.query), {
      method: options.method ?? 'GET',
      headers,
      body,
      signal: options.signal,
    });
  } catch (error) {
    if (options.signal?.aborted) throw new ApiError(0, ABORTED, 'aborted');
    throw new ApiError(0, NETWORK_ERROR, error instanceof Error ? error.message : 'network');
  }
}

/** Typed JSON request against `/v1`. Retries once after refreshing an expired access token. */
export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  let response = await send(path, options);

  if (response.status === 401 && !options.anonymous) {
    refreshing ??= refreshTokens().finally(() => {
      refreshing = null;
    });
    if (await refreshing) {
      response = await send(path, options);
    } else {
      await tokenStorage.clear();
      onUnauthorized?.();
    }
  }

  if (!response.ok) throw await toApiError(response);
  if (response.status === 204 || response.status === 202) {
    const text = await response.text();
    return (text ? JSON.parse(text) : undefined) as T;
  }
  return (await response.json()) as T;
}
