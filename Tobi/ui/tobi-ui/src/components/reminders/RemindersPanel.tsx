"use client";

/**
 * RemindersPanel  — full reminders management UI (Phase 0)
 *
 * Features:
 *  - List upcoming / all reminders
 *  - Create new reminder (text + datetime picker + recurrence + alarm toggle)
 *  - Voice-record a reminder clip (own-voice playback mode)
 *  - Dismiss / snooze / delete actions per row
 *  - Play back own-voice audio clips inline
 */

import {
  useState,
  useEffect,
  useCallback,
  useRef,
  ChangeEvent,
} from "react";
import { remindersApi, Reminder, ReminderCreate } from "@/hooks/useTobiApi";

// ─────────────────────── helpers ─────────────────────────────────────────────

function formatDue(ts: number): string {
  const now = Date.now() / 1000;
  const delta = ts - now;
  const abs = Math.abs(delta);

  if (delta < 0) return "overdue";
  if (abs < 60) return "now";
  if (abs < 3600) return `in ${Math.round(abs / 60)}m`;

  const d = new Date(ts * 1000);
  const today = new Date();
  const tomorrow = new Date(today);
  tomorrow.setDate(today.getDate() + 1);

  const timeStr = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  if (d.toDateString() === today.toDateString()) return `Today ${timeStr}`;
  if (d.toDateString() === tomorrow.toDateString()) return `Tomorrow ${timeStr}`;
  return d.toLocaleDateString([], { weekday: "short", month: "short", day: "numeric" }) + ` ${timeStr}`;
}

function statusColour(r: Reminder): string {
  if (r.status === "fired") return "text-amber-400";
  const delta = r.due_at - Date.now() / 1000;
  if (delta < 0) return "text-red-400/80";
  if (delta < 1800) return "text-amber-400/80";
  return "text-tobi-cyan/70";
}

// ISO-8601 local datetime string for <input type="datetime-local">
function toDatetimeLocal(isoOrEmpty: string): string {
  if (!isoOrEmpty) return "";
  try {
    const d = new Date(isoOrEmpty);
    const pad = (n: number) => String(n).padStart(2, "0");
    return (
      `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}` +
      `T${pad(d.getHours())}:${pad(d.getMinutes())}`
    );
  } catch {
    return "";
  }
}

function datetimeLocalToIso(val: string): string {
  if (!val) return "";
  return new Date(val).toISOString().slice(0, 19);
}

// ─────────────────────── sub-components ──────────────────────────────────────

function RecurrenceBadge({ value }: { value: string }) {
  if (value === "none") return null;
  const labels: Record<string, string> = {
    daily: "daily",
    weekly: "wkly",
    weekdays: "wkdays",
    monthly: "mo",
  };
  return (
    <span className="text-3xs font-mono bg-white/[0.05] text-white/40 px-1.5 py-0.5 rounded-full border border-white/[0.06]">
      ↻ {labels[value] ?? value}
    </span>
  );
}

function AlarmBadge({ isAlarm }: { isAlarm: boolean }) {
  if (!isAlarm) return null;
  return (
    <span className="text-3xs font-mono bg-amber-400/10 text-amber-400/70 px-1.5 py-0.5 rounded-full border border-amber-400/20">
      alarm
    </span>
  );
}

// ─────────────────────── create form ─────────────────────────────────────────

interface CreateFormProps {
  onCreated: (r: Reminder) => void;
  onCancel: () => void;
}

function CreateForm({ onCreated, onCancel }: CreateFormProps) {
  const [content, setContent] = useState("");
  const [dueLocal, setDueLocal] = useState("");
  const [isAlarm, setIsAlarm] = useState(false);
  const [recurrence, setRecurrence] = useState("none");
  const [playbackMode, setPlaybackMode] = useState<"tobi_voice" | "own_voice">("tobi_voice");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  // Voice recording state
  const [recording, setRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);
  const createdIdRef = useRef<number | null>(null);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      chunksRef.current = [];
      mr.ondataavailable = (e) => chunksRef.current.push(e.data);
      mr.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        setAudioBlob(blob);
        setAudioUrl(URL.createObjectURL(blob));
        setPlaybackMode("own_voice");
        stream.getTracks().forEach((t) => t.stop());
      };
      mr.start();
      mediaRef.current = mr;
      setRecording(true);
    } catch (err) {
      setError("Microphone access denied.");
    }
  }, []);

  const stopRecording = useCallback(() => {
    mediaRef.current?.stop();
    setRecording(false);
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!content.trim()) { setError("Reminder text is required."); return; }
    if (!dueLocal) { setError("Due date/time is required."); return; }

    setSaving(true);
    setError("");
    try {
      const payload: ReminderCreate = {
        content: content.trim(),
        due_at_iso: datetimeLocalToIso(dueLocal),
        is_alarm: isAlarm,
        recurrence,
        playback_mode: playbackMode,
      };
      const created = await remindersApi.create(payload);
      createdIdRef.current = created.id;

      // Upload voice clip if recorded
      if (audioBlob && created.id) {
        const token = sessionStorage.getItem("Tobi_auth_token") ?? "";
        const form = new FormData();
        form.append("audio", audioBlob, "reminder.webm");
        const base = window.location.hostname === "localhost"
          ? `http://localhost:8741`
          : `${window.location.origin}/Tobi-api`;
        await fetch(`${base}/reminders/${created.id}/audio`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "X-Tobi-Client": "tobi-ui",
          },
          body: form,
        });
      }

      onCreated(created);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to create reminder.");
    } finally {
      setSaving(false);
    }
  }, [content, dueLocal, isAlarm, recurrence, playbackMode, audioBlob, onCreated]);

  return (
    <div className="bg-white/[0.03] border border-white/[0.07] rounded-xl p-4 space-y-3">
      <div className="text-2xs font-medium text-white/50 uppercase tracking-[0.1em]">
        New Reminder
      </div>

      {/* Content */}
      <textarea
        value={content}
        onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setContent(e.target.value)}
        placeholder="What should I remind you about?"
        rows={2}
        className="w-full bg-white/[0.04] border border-white/[0.07] rounded-lg px-3 py-2.5 text-sm text-white/80 placeholder-white/20 resize-none focus:outline-none focus:border-cyan-500/40 focus:bg-white/[0.06] transition-all"
      />

      {/* Date/time */}
      <input
        type="datetime-local"
        value={dueLocal}
        onChange={(e: ChangeEvent<HTMLInputElement>) => setDueLocal(e.target.value)}
        className="w-full bg-white/[0.04] border border-white/[0.07] rounded-lg px-3 py-2.5 text-sm text-white/70 focus:outline-none focus:border-cyan-500/40 transition-all [color-scheme:dark]"
      />

      {/* Recurrence + Alarm row */}
      <div className="flex flex-wrap gap-2 items-center">
        <select
          value={recurrence}
          onChange={(e: ChangeEvent<HTMLSelectElement>) => setRecurrence(e.target.value)}
          className="bg-white/[0.04] border border-white/[0.07] rounded-lg px-2.5 py-1.5 text-xs text-white/60 focus:outline-none focus:border-cyan-500/40 transition-all [color-scheme:dark]"
        >
          <option value="none">Once</option>
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
          <option value="weekdays">Weekdays</option>
          <option value="monthly">Monthly</option>
        </select>

        <label className="flex items-center gap-2 cursor-pointer select-none">
          <div
            onClick={() => setIsAlarm((v) => !v)}
            className={`w-8 h-4 rounded-full transition-colors duration-200 relative ${isAlarm ? "bg-amber-400/60" : "bg-white/10"}`}
          >
            <span className={`absolute top-0.5 w-3 h-3 rounded-full bg-white transition-all duration-200 ${isAlarm ? "left-4" : "left-0.5"}`} />
          </div>
          <span className="text-xs text-white/50">Full alarm</span>
        </label>
      </div>

      {/* Voice recording */}
      <div className="flex items-center gap-2">
        {!recording && !audioUrl && (
          <button
            onClick={startRecording}
            className="flex items-center gap-1.5 text-xs text-white/40 hover:text-cyan-400/70 transition-colors"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z" />
              <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
              <line x1="12" y1="19" x2="12" y2="23" />
              <line x1="8" y1="23" x2="16" y2="23" />
            </svg>
            Record voice clip
          </button>
        )}
        {recording && (
          <button
            onClick={stopRecording}
            className="flex items-center gap-1.5 text-xs text-red-400/80 hover:text-red-400 transition-colors animate-pulse"
          >
            <span className="w-2 h-2 rounded-full bg-red-400 animate-ping" />
            Stop recording
          </button>
        )}
        {audioUrl && (
          <div className="flex items-center gap-2">
            <audio src={audioUrl} controls className="h-7 max-w-[160px]" />
            <button
              onClick={() => { setAudioBlob(null); setAudioUrl(null); setPlaybackMode("tobi_voice"); }}
              className="text-xs text-white/30 hover:text-red-400/70 transition-colors"
              aria-label="Remove recording"
            >
              ✕
            </button>
            <span className="text-3xs text-cyan-400/60">own voice ✓</span>
          </div>
        )}
      </div>

      {error && (
        <p className="text-xs text-red-400/80">{error}</p>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 pt-1">
        <button
          onClick={handleSubmit}
          disabled={saving}
          className="flex-1 bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/25 text-cyan-300/80 text-xs font-medium rounded-lg py-2 transition-all disabled:opacity-40"
        >
          {saving ? "Saving…" : "Set reminder"}
        </button>
        <button
          onClick={onCancel}
          className="px-3 py-2 text-xs text-white/30 hover:text-white/60 transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}

// ─────────────────────── reminder row ────────────────────────────────────────

interface ReminderRowProps {
  reminder: Reminder;
  onDismiss: (id: number) => void;
  onSnooze: (id: number) => void;
  onDelete: (id: number) => void;
}

function ReminderRow({ reminder: r, onDismiss, onSnooze, onDelete }: ReminderRowProps) {
  const [expanded, setExpanded] = useState(false);
  const audioUrl = r.audio_url ? remindersApi.audioUrl(r.id) : null;

  return (
    <div
      className={`group relative rounded-xl border transition-all duration-200 ${
        r.status === "fired"
          ? "bg-amber-400/5 border-amber-400/15"
          : "bg-white/[0.025] border-white/[0.05] hover:border-white/[0.09] hover:bg-white/[0.04]"
      }`}
    >
      <button
        className="w-full text-left px-4 py-3 flex items-start gap-3"
        onClick={() => setExpanded((v) => !v)}
        aria-expanded={expanded}
      >
        {/* Status dot */}
        <div className={`mt-1.5 w-1.5 h-1.5 rounded-full flex-shrink-0 ${
          r.status === "fired" ? "bg-amber-400 animate-pulse" :
          r.due_at - Date.now() / 1000 < 0 ? "bg-red-400/80" :
          r.due_at - Date.now() / 1000 < 1800 ? "bg-amber-400/70" :
          "bg-cyan-400/50"
        }`} />

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`text-xs font-medium ${statusColour(r)}`}>
              {formatDue(r.due_at)}
            </span>
            <RecurrenceBadge value={r.recurrence} />
            <AlarmBadge isAlarm={r.is_alarm} />
            {r.audio_url && (
              <span className="text-3xs text-cyan-400/50">🎙</span>
            )}
          </div>
          <p className="text-sm text-white/70 mt-0.5 leading-snug line-clamp-2">
            {r.content}
          </p>
        </div>

        {/* Chevron */}
        <svg
          width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor"
          strokeWidth="1.5" className={`flex-shrink-0 mt-1 text-white/20 transition-transform duration-200 ${expanded ? "rotate-180" : ""}`}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {/* Expanded row actions */}
      {expanded && (
        <div className="px-4 pb-3 pt-0 space-y-2.5 border-t border-white/[0.04] mt-0">
          {audioUrl && (
            <div className="pt-2">
              <p className="text-3xs text-white/30 mb-1 uppercase tracking-wider">Voice clip</p>
              <audio src={audioUrl} controls className="h-8 w-full max-w-xs" />
            </div>
          )}
          <div className="flex items-center gap-2 pt-1 flex-wrap">
            {(r.status === "fired" || r.status === "pending" || r.status === "snoozed") && (
              <>
                <button
                  onClick={() => onDismiss(r.id)}
                  className="text-xs px-3 py-1.5 rounded-lg bg-white/[0.04] hover:bg-white/[0.08] text-white/50 hover:text-white/80 transition-all border border-white/[0.06]"
                >
                  Dismiss
                </button>
                <button
                  onClick={() => onSnooze(r.id)}
                  className="text-xs px-3 py-1.5 rounded-lg bg-white/[0.04] hover:bg-amber-400/15 text-white/50 hover:text-amber-300/80 transition-all border border-white/[0.06] hover:border-amber-400/20"
                >
                  Snooze 10m
                </button>
              </>
            )}
            <button
              onClick={() => onDelete(r.id)}
              className="text-xs px-3 py-1.5 rounded-lg bg-white/[0.04] hover:bg-red-400/10 text-white/30 hover:text-red-400/70 transition-all border border-white/[0.06] hover:border-red-400/20 ml-auto"
            >
              Delete
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─────────────────────── main panel ──────────────────────────────────────────

export default function RemindersPanel() {
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showAll, setShowAll] = useState(false);
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await remindersApi.list(!showAll, showAll ? 8760 : 48);
      setReminders(data.reminders);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Failed to load reminders.");
    } finally {
      setLoading(false);
    }
  }, [showAll]);

  useEffect(() => { load(); }, [load]);

  // Auto-refresh every 60 s so fired reminders update
  useEffect(() => {
    const id = setInterval(load, 60_000);
    return () => clearInterval(id);
  }, [load]);

  const handleDismiss = useCallback(async (id: number) => {
    try {
      await remindersApi.dismiss(id);
      setReminders((prev) => prev.filter((r) => r.id !== id));
    } catch { /* silently ignore */ }
  }, []);

  const handleSnooze = useCallback(async (id: number) => {
    try {
      await remindersApi.snooze(id, 10);
      await load();
    } catch { /* silently ignore */ }
  }, [load]);

  const handleDelete = useCallback(async (id: number) => {
    try {
      await remindersApi.delete(id);
      setReminders((prev) => prev.filter((r) => r.id !== id));
    } catch { /* silently ignore */ }
  }, []);

  const handleCreated = useCallback((r: Reminder) => {
    setCreating(false);
    setReminders((prev) => [r, ...prev].sort((a, b) => a.due_at - b.due_at));
  }, []);

  const firedCount = reminders.filter((r) => r.status === "fired").length;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-white/[0.04] bg-white/[0.015] backdrop-blur-lg flex-shrink-0">
        <div className="flex items-center gap-2.5">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="text-amber-400/60">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
            <path d="M13.73 21a2 2 0 0 1-3.46 0" />
          </svg>
          <span className="text-2xs font-medium text-white/50 uppercase tracking-[0.12em]">
            Reminders
          </span>
          {firedCount > 0 && (
            <span className="text-3xs bg-amber-400/20 text-amber-400/80 px-1.5 py-0.5 rounded-full font-mono border border-amber-400/20">
              {firedCount} fired
            </span>
          )}
          {reminders.length > 0 && (
            <span className="text-3xs text-white/20 font-mono">
              {reminders.length}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => { setShowAll((v) => !v); }}
            className="text-3xs text-white/30 hover:text-white/60 transition-colors"
          >
            {showAll ? "Upcoming" : "All"}
          </button>
          <button
            onClick={load}
            className="text-3xs text-white/30 hover:text-cyan-400/60 transition-colors"
            aria-label="Refresh"
          >
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="1 4 1 10 7 10" />
              <path d="M3.51 15a9 9 0 1 0 .49-3.65" />
            </svg>
          </button>
          <button
            onClick={() => setCreating(true)}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-cyan-500/15 hover:bg-cyan-500/25 border border-cyan-500/25 text-cyan-300/80 transition-all"
          >
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="5" x2="12" y2="19" /><line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            New
          </button>
        </div>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-2 tobi-scrollbar">
        {creating && (
          <CreateForm
            onCreated={handleCreated}
            onCancel={() => setCreating(false)}
          />
        )}

        {loading && (
          <div className="flex items-center justify-center py-10">
            <div className="w-5 h-5 border-2 border-cyan-400/20 border-t-cyan-400/70 rounded-full animate-spin" />
          </div>
        )}

        {!loading && error && (
          <div className="text-xs text-red-400/70 text-center py-6">{error}</div>
        )}

        {!loading && !error && reminders.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 gap-3 text-center">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" className="text-white/10">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
            <p className="text-sm text-white/25">No reminders yet.</p>
            <p className="text-xs text-white/15">
              Say "remind me to…" or tap New above.
            </p>
          </div>
        )}

        {!loading && reminders.map((r) => (
          <ReminderRow
            key={r.id}
            reminder={r}
            onDismiss={handleDismiss}
            onSnooze={handleSnooze}
            onDelete={handleDelete}
          />
        ))}
      </div>
    </div>
  );
}
