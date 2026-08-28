"use client";

/**
 * useTobiApi — lightweight fetch wrapper for TOBI REST endpoints.
 *
 * Auto-injects the auth token from sessionStorage, uses the same
 * API base URL logic as useAuth, and includes the X-Tobi-Client
 * CSRF header required for mutating requests.
 */

function getApiBase(): string {
  if (typeof window === "undefined") return "http://localhost:8741";
  const { hostname, port, protocol, origin } = window.location;
  const isLocal = hostname === "localhost" || hostname === "127.0.0.1";
  if ((!port || port === "443" || port === "80") && !isLocal) {
    return `${origin}/Tobi-api`;
  }
  return `${protocol}//${hostname}:8741`;
}

function getToken(): string | null {
  try {
    return sessionStorage.getItem("Tobi_auth_token");
  } catch {
    return null;
  }
}

type Method = "GET" | "POST" | "PATCH" | "PUT" | "DELETE";

async function apiFetch<T = unknown>(
  path: string,
  method: Method = "GET",
  body?: unknown
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-Tobi-Client": "tobi-ui",
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${getApiBase()}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: res.statusText }));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

// ── Reminders ────────────────────────────────────────────────────────────────

export interface Reminder {
  id: number;
  content: string;
  due_at: number;
  due_at_iso: string;
  audio_url: string | null;
  playback_mode: "own_voice" | "tobi_voice";
  is_alarm: boolean;
  recurrence: "none" | "daily" | "weekly" | "weekdays" | "monthly";
  status: "pending" | "snoozed" | "fired" | "dismissed" | "deleted";
  snooze_until: number | null;
  created_at: number;
  last_fired_at: number | null;
}

export interface ReminderCreate {
  content: string;
  due_at_iso: string;
  is_alarm?: boolean;
  recurrence?: string;
  playback_mode?: string;
}

export const remindersApi = {
  list: (upcoming = true, hours = 48) =>
    apiFetch<{ reminders: Reminder[]; count: number }>(
      `/reminders?upcoming=${upcoming}&hours=${hours}`
    ),
  create: (data: ReminderCreate) =>
    apiFetch<Reminder>("/reminders", "POST", data),
  update: (id: number, data: Partial<ReminderCreate> & { is_alarm?: boolean }) =>
    apiFetch<Reminder>(`/reminders/${id}`, "PATCH", data),
  dismiss: (id: number) =>
    apiFetch<{ status: string }>(`/reminders/${id}/dismiss`, "POST"),
  snooze: (id: number, minutes = 10) =>
    apiFetch<{ status: string; wake_at: string }>(`/reminders/${id}/snooze`, "POST", { minutes }),
  delete: (id: number) =>
    apiFetch<{ status: string }>(`/reminders/${id}`, "DELETE"),
  audioUrl: (id: number) => `${getApiBase()}/reminders/${id}/audio?token=${getToken() ?? ""}`,
};

// ── Facts / Memory ────────────────────────────────────────────────────────────

export interface UserFact {
  category: string;
  subject: string;
  value: string;
  confidence: number;
  source?: string;
  last_reinforced?: number;
  reinforcement_count?: number;
}

export interface MemoryStats {
  vector_store: { backend: string; count: number };
  facts: {
    total_facts: number;
    high_confidence: number;
    by_category: Record<string, number>;
    avg_confidence: number;
  };
  preferences: { total_patterns: number };
}

export const memoryApi = {
  stats: () => apiFetch<MemoryStats>("/health"),
  facts: () =>
    apiFetch<{ reminders?: never }>("/chat").then(() => {
      // facts come from the /chat endpoint indirectly; use the dedicated tool endpoint
      return apiFetch<{ text: string }>("/chat", "POST", {
        message: "__internal_get_facts__",
      });
    }),
};

// ── Digest ────────────────────────────────────────────────────────────────────

export interface DigestData {
  date_label: string;
  greeting: string;
  priorities: Array<{ type: string; content: string; project?: string; due?: string }>;
  reminders: Array<{ id: number; content: string; due_label: string; is_alarm: boolean }>;
  drift_nudges: Array<{ subject: string; value: string; days_since: number }>;
  facts_summary: UserFact[];
  insight: string;
  generated_at: number;
  stats: { total_reminders: number; stale_goals: number; open_tasks: number };
}

export const digestApi = {
  get: () => apiFetch<DigestData>("/digest"),
  wakeBriefing: () => apiFetch<{ text: string; priorities: string[]; word_count: number }>("/digest/wake-briefing"),
};
