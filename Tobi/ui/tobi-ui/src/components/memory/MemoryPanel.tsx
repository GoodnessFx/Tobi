"use client";

/**
 * MemoryPanel  — displays TOBI's known facts and today's digest (Phase 0)
 *
 * Tabs:
 *  - Digest   : today's morning digest (priorities, reminders, drift nudges, insight)
 *  - Facts    : all extracted user facts with category + confidence
 */

import { useState, useEffect, useCallback } from "react";
import { digestApi, DigestData } from "@/hooks/useTobiApi";

// ─────────────────────── helpers ─────────────────────────────────────────────

const CATEGORY_COLOURS: Record<string, string> = {
  personal:     "text-cyan-800 bg-cyan-50 border-cyan-200",
  work:         "text-blue-800 bg-blue-50 border-blue-200",
  preference:   "text-violet-800 bg-violet-50 border-violet-200",
  location:     "text-emerald-800 bg-emerald-50 border-emerald-200",
  relationship: "text-pink-800 bg-pink-50 border-pink-200",
  habit:        "text-orange-800 bg-orange-50 border-orange-200",
  skill_gap:    "text-amber-800 bg-amber-50 border-amber-200",
  goal:         "text-yellow-800 bg-yellow-50 border-yellow-200",
  explicit:     "text-Tobi-text-sub bg-Tobi-surface-alt border-Tobi-border",
};

function categoryStyle(cat: string): string {
  return CATEGORY_COLOURS[cat] ?? "text-Tobi-text-sub bg-Tobi-surface-alt border-Tobi-border";
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const colour =
    pct >= 80 ? "bg-emerald-400/50" :
    pct >= 50 ? "bg-cyan-400/40" :
    "bg-slate-200";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1 bg-slate-100 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-500 ${colour}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-3xs font-mono text-Tobi-text-muted tabular-nums w-7">{pct}%</span>
    </div>
  );
}

// ─────────────────────── Digest tab ──────────────────────────────────────────

function DigestTab({ token }: { token: string | null }) {
  const [data, setData] = useState<DigestData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const d = await digestApi.get();
      setData(d);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load digest.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return (
    <div className="flex items-center justify-center py-16">
      <div className="w-5 h-5 border-2 border-cyan-400/20 border-t-cyan-400/60 rounded-full animate-spin" />
    </div>
  );

  if (error) return (
    <div className="text-xs text-red-700 text-center py-10">{error}</div>
  );

  if (!data) return null;

  return (
    <div className="space-y-4">
      {/* Header greeting */}
      <div className="bg-Tobi-surface border border-Tobi-border rounded-xl p-4">
        <div className="text-3xs text-Tobi-text-muted uppercase tracking-[0.15em] mb-1">{data.date_label}</div>
        <div className="text-base font-semibold text-Tobi-text">{data.greeting}, sir.</div>
        {data.insight && (
          <p className="mt-2 text-xs text-cyan-800 leading-relaxed italic border-l-2 border-cyan-300 pl-3">
            &quot;{data.insight}&quot;
          </p>
        )}
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-2">
        {[
          { label: "Open tasks", value: data.stats.open_tasks },
          { label: "Reminders", value: data.stats.total_reminders },
          { label: "Stale goals", value: data.stats.stale_goals },
        ].map(({ label, value }) => (
          <div key={label} className="bg-Tobi-surface border border-Tobi-border rounded-xl p-3 text-center">
            <div className="text-xl font-mono font-semibold text-Tobi-text tabular-nums">{value}</div>
            <div className="text-3xs text-Tobi-text-muted mt-0.5">{label}</div>
          </div>
        ))}
      </div>

      {/* Priorities */}
      {data.priorities.length > 0 && (
        <div>
          <div className="text-3xs text-Tobi-text-muted uppercase tracking-[0.15em] mb-2 px-1">Top priorities</div>
          <div className="space-y-1.5">
            {data.priorities.map((p, i) => (
              <div key={i} className="flex items-start gap-3 bg-Tobi-surface border border-Tobi-border rounded-xl px-3 py-2.5">
                <span className="text-3xs font-mono text-Tobi-text-muted mt-0.5 w-3 flex-shrink-0">{i + 1}.</span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-Tobi-text leading-snug">{p.content}</p>
                  {p.project && (
                    <span className="text-3xs text-Tobi-text-muted">{p.project}</span>
                  )}
                </div>
                <span className={`text-3xs px-1.5 py-0.5 rounded-full border flex-shrink-0 ${
                  p.type === "goal"
                    ? "text-yellow-800 bg-yellow-50 border-yellow-200"
                    : "text-Tobi-text-sub bg-Tobi-surface-alt border-Tobi-border"
                }`}>
                  {p.type}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Upcoming reminders */}
      {data.reminders.length > 0 && (
        <div>
          <div className="text-3xs text-Tobi-text-muted uppercase tracking-[0.15em] mb-2 px-1">Due today</div>
          <div className="space-y-1.5">
            {data.reminders.map((r) => (
              <div key={r.id} className="flex items-center gap-3 bg-Tobi-surface border border-Tobi-border rounded-xl px-3 py-2.5">
                {r.is_alarm && (
                  <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-amber-700 flex-shrink-0">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
                    <path d="M13.73 21a2 2 0 0 1-3.46 0" />
                  </svg>
                )}
                <p className="flex-1 text-sm text-Tobi-text-sub truncate">{r.content}</p>
                <span className="text-3xs font-mono text-cyan-800 whitespace-nowrap">{r.due_label}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Drift nudges */}
      {data.drift_nudges.length > 0 && (
        <div>
          <div className="text-3xs text-amber-800 uppercase tracking-[0.15em] mb-2 px-1">Slipping</div>
          <div className="space-y-1.5">
            {data.drift_nudges.map((n, i) => (
              <div key={i} className="flex items-center gap-3 bg-amber-50 border border-amber-200 rounded-xl px-3 py-2.5">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-amber-700 flex-shrink-0">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                  <line x1="12" y1="9" x2="12" y2="13" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
                <p className="flex-1 text-sm text-amber-900 truncate">{n.value}</p>
                <span className="text-3xs font-mono text-amber-800 whitespace-nowrap">{n.days_since}d ago</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <button
        onClick={load}
        className="w-full text-xs text-Tobi-text-muted hover:text-Tobi-text transition-colors py-2"
      >
        Refresh digest
      </button>
    </div>
  );
}

// ─────────────────────── Facts tab ───────────────────────────────────────────

interface FactsTabProps {
  facts: DigestData["facts_summary"];
}

function FactsTab({ facts }: FactsTabProps) {
  const [filter, setFilter] = useState("");

  const filtered = facts.filter((f) =>
    !filter ||
    f.value.toLowerCase().includes(filter.toLowerCase()) ||
    f.subject.toLowerCase().includes(filter.toLowerCase()) ||
    f.category.toLowerCase().includes(filter.toLowerCase())
  );

  // Group by category
  const grouped: Record<string, typeof facts> = {};
  for (const f of filtered) {
    (grouped[f.category] = grouped[f.category] ?? []).push(f);
  }

  if (facts.length === 0) return (
    <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" className="text-Tobi-text-muted/50">
        <circle cx="12" cy="12" r="3" />
        <path d="M20.188 10.934c.2.646.312 1.329.312 2.066s-.112 1.42-.312 2.066l2.154 1.629a12 12 0 0 1-2.598 4.5l-2.548-.965c-1.063.895-2.278 1.58-3.618 1.997l-.396 2.656a12 12 0 0 1-5.163 0l-.397-2.656a9.94 9.94 0 0 1-3.617-1.997l-2.548.965a12 12 0 0 1-2.598-4.5l2.154-1.629A9.965 9.965 0 0 1 1.5 12c0-.737.112-1.42.312-2.066L-.342 8.305a12 12 0 0 1 2.598-4.5l2.548.965a9.94 9.94 0 0 1 3.617-1.997L8.918 0a12 12 0 0 1 5.163 0l.397 2.773a9.94 9.94 0 0 1 3.618 1.997l2.548-.965a12 12 0 0 1 2.598 4.5L20.188 10.934z" />
      </svg>
      <p className="text-sm text-Tobi-text-muted">No facts learned yet.</p>
      <p className="text-xs text-Tobi-text-dim">Facts are extracted automatically as you talk to TOBI.</p>
    </div>
  );

  return (
    <div className="space-y-4">
      {/* Search */}
      <input
        type="text"
        value={filter}
        onChange={(e) => setFilter(e.target.value)}
        placeholder="Search facts…"
        className="w-full bg-white border border-Tobi-border rounded-lg px-3 py-2 text-sm text-Tobi-text placeholder-Tobi-text-muted focus:outline-none focus:border-Tobi-cyan/50 transition-all"
      />

      <div className="text-3xs text-Tobi-text-muted px-1">
        {filtered.length} of {facts.length} facts
      </div>

      {Object.entries(grouped).map(([category, catFacts]) => (
        <div key={category}>
          <div className="flex items-center gap-2 mb-2 px-1">
            <span className={`text-3xs px-2 py-0.5 rounded-full border font-medium uppercase tracking-[0.1em] ${categoryStyle(category)}`}>
              {category.replace("_", " ")}
            </span>
            <span className="text-3xs text-Tobi-text-muted font-mono">{catFacts.length}</span>
          </div>
          <div className="space-y-1.5">
            {catFacts.map((f, i) => (
              <div key={i} className="bg-Tobi-surface border border-Tobi-border rounded-xl px-3 py-2.5 space-y-1.5">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="text-3xs text-Tobi-text-muted mb-0.5">{f.subject.replace(/_/g, " ")}</div>
                    <div className="text-sm text-Tobi-text">{f.value}</div>
                  </div>
                </div>
                <ConfidenceBar value={f.confidence} />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

// ─────────────────────── main panel ──────────────────────────────────────────

interface MemoryPanelProps {
  token: string | null;
}

type Tab = "digest" | "facts";

export default function MemoryPanel({ token }: MemoryPanelProps) {
  const [tab, setTab] = useState<Tab>("digest");
  const [digestData, setDigestData] = useState<DigestData | null>(null);
  const [digestLoading, setDigestLoading] = useState(true);

  // Pre-load digest so Facts tab can show facts_summary without extra fetch
  useEffect(() => {
    digestApi.get()
      .then(setDigestData)
      .catch(() => {})
      .finally(() => setDigestLoading(false));
  }, []);

  const tabs: { id: Tab; label: string; icon: string[] }[] = [
    {
      id: "digest",
      label: "Digest",
      icon: ["M9 11l3 3L22 4", "M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"],
    },
    {
      id: "facts",
      label: "Facts",
      icon: [
        "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z",
        "M12 6v6l4 2",
      ],
    },
  ];

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-Tobi-border bg-white/90 backdrop-blur-lg flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-Tobi-cyan">
            <ellipse cx="12" cy="5" rx="9" ry="3" />
            <path d="M21 12c0 1.66-4.03 3-9 3S3 13.66 3 12" />
            <path d="M3 5v14c0 1.66 4.03 3 9 3s9-1.34 9-3V5" />
          </svg>
          <span className="text-2xs font-medium text-Tobi-text-sub uppercase tracking-[0.12em]">Memory</span>
          {digestData && (
            <span className="text-3xs text-Tobi-text-muted font-mono">
              {digestData.facts_summary.length} facts
            </span>
          )}
        </div>

        {/* Tab switcher */}
        <div className="flex items-center gap-0.5 bg-Tobi-surface-alt border border-Tobi-border rounded-lg p-0.5">
          {tabs.map(({ id, label, icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-2xs font-medium transition-all duration-200 ${
                tab === id
                  ? "bg-white text-Tobi-text border border-Tobi-border shadow-sm"
                  : "text-Tobi-text-dim hover:text-Tobi-text"
              }`}
            >
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                {icon.map((d, i) => <path key={i} d={d} />)}
              </svg>
              {label}
            </button>
          ))}
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto px-4 py-4 tobi-scrollbar">
        {tab === "digest" && <DigestTab token={token} />}
        {tab === "facts" && (
          digestLoading
            ? <div className="flex items-center justify-center py-16"><div className="w-5 h-5 border-2 border-cyan-400/20 border-t-cyan-400/60 rounded-full animate-spin" /></div>
            : <FactsTab facts={digestData?.facts_summary ?? []} />
        )}
      </div>
    </div>
  );
}
