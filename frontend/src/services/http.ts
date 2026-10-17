import type { ApiError, ApiResponse } from "../types/api";

const API_BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";

export class ApiRequestError extends Error {
  constructor(public readonly status: number, public readonly payload: ApiError) {
    super(payload.error?.message ?? `请求失败（HTTP ${status}）`);
  }
}

export async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<ApiResponse<T>> {
  const token = localStorage.getItem("activity-reference-token");
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401) localStorage.removeItem("activity-reference-token");
    throw new ApiRequestError(response.status, payload as ApiError);
  }
  return payload as ApiResponse<T>;
}
