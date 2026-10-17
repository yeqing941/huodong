export type Role = "user" | "operator" | "admin";

export interface User { id: string; username: string; email: string; role: Role; status: "active" | "disabled"; }
export interface ApiResponse<T> { data: T; meta: Record<string, unknown>; }
export interface GameTypeOption { id: string; name: string; }
export interface TagOption { id: string; name: string; parent_id: string | null; level: number; is_active?: boolean; children?: TagOption[]; }
export interface Activity { id: string; source_url: string; source_site: string; game_name: string; activity_name: string; activity_start: string | null; activity_end: string | null; status: string; description: string; is_favorite: boolean; game_type: GameTypeOption; tags: Array<{ id: string; name: string; level: number }>; screenshots: Array<{ id: string; url: string; caption: string; sort_order: number }>; }
export interface ActivityPage { items: Activity[]; page: number; page_size: number; total: number; total_pages: number; }
export interface ReviewRecord { id: string; activity_id: string; status: string; original_data: { activity_name?: string; [key: string]: unknown }; candidate_tags: Array<{ id: string; name: string; confidence?: number; reason?: string }>; ai_error: string; operator_note: string; admin_note: string; }
export interface CrawlerConfig { id: number; source: string; rule_summary: string; game_scope: string[]; cron: string; enabled: boolean; consecutive_failures: number; auto_paused: boolean; last_run_at: string | null; }
export interface CrawlerTask { id: number; config_id: number; status: string; trigger_type: string; source: string; game_scope: string[]; discovered_count: number; new_count: number; duplicate_count: number; failed_count: number; pending_tagging_count: number; started_at: string | null; finished_at: string | null; }
export interface ApiError { error: { code: string; message: string; details?: unknown; request_id?: string; }; }
