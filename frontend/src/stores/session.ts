import { reactive } from "vue";
import type { User } from "../types/api";
import { request } from "../services/http";

const TOKEN_KEY = "activity-reference-token";

export const session = reactive<{ token: string | null; user: User | null; loading: boolean }>({
  token: localStorage.getItem(TOKEN_KEY),
  user: null,
  loading: false,
});

export async function restoreSession() {
  if (!session.token) return null;
  session.loading = true;
  try {
    const response = await request<User>("/auth/me");
    session.user = response.data;
    return session.user;
  } catch {
    clearSession();
    return null;
  } finally {
    session.loading = false;
  }
}

export function setSession(token: string, user: User) {
  localStorage.setItem(TOKEN_KEY, token);
  session.token = token;
  session.user = user;
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  session.token = null;
  session.user = null;
}
