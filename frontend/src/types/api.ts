export type Role = "user" | "operator" | "admin";

export interface User {
  id: string;
  username: string;
  email: string;
  role: Role;
  status: "active" | "disabled";
}

export interface ApiResponse<T> {
  data: T;
  meta: Record<string, unknown>;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: unknown;
    request_id?: string;
  };
}
