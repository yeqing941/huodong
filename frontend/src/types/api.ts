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

export interface Activity {
  id: string;
  game_name: string;
  activity_name: string;
  status: string;
  description: string;
  is_favorite: boolean;
  game_type: { id: string; name: string };
  tags: Array<{ id: string; name: string; level: number }>;
  screenshots: Array<{ id: string; url: string; caption: string; sort_order: number }>;
}

export interface ActivityPage {
  items: Activity[];
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface ApiError {
  error: {
    code: string;
    message: string;
    details?: unknown;
    request_id?: string;
  };
}
