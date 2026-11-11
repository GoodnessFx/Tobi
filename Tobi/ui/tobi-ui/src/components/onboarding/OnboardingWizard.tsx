"use client";

import { useCallback, useEffect, useState } from "react";
import {
  GoogleWorkspaceStatus,
  OnboardingProfile,
  onboardingApi,
} from "@/hooks/useTobiApi";
import { CharacterStyle } from "@/lib/types";

interface OnboardingPreferences {
  nickname: string;
  character: CharacterStyle;
  voiceInputEnabled: boolean;
}

interface OnboardingWizardProps {
  onComplete: (preferences: OnboardingPreferences) => void;
}

const VOICES = [
  { id: "bf_emma", label: "Emma", description: "British · warm" },
  { id: "bf_isabella", label: "Isabella", description: "British · clear" },
  { id: "bm_george", label: "George", description: "British · composed" },
  { id: "bm_lewis", label: "Lewis", description: "British · relaxed" },
  { id: "af_heart", label: "Heart", description: "American · bright" },
];

const PROFILE_KEYS: Array<"nickname" | "voice" | "character" | "voice_input_enabled"> = [
  "nickname",
  "voice",
  "character",
  "voice_input_enabled",
];

export default function OnboardingWizard({ onComplete }: OnboardingWizardProps) {
  const [step, setStep] = useState(0);
  const [nickname, setNickname] = useState("");
  const [voice, setVoice] = useState("bf_emma");
  const [character, setCharacter] = useState<CharacterStyle>("orb");
  const [voiceInputEnabled, setVoiceInputEnabled] = useState(true);
  const [notificationPermission, setNotificationPermission] =
    useState<NotificationPermission | "unsupported">("default");
  const [ttsEngine, setTtsEngine] = useState("");
  const [currentTtsVoice, setCurrentTtsVoice] = useState("");
  const [googleStatus, setGoogleStatus] = useState<GoogleWorkspaceStatus | null>(null);
  const [googleError, setGoogleError] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [connectingGoogle, setConnectingGoogle] = useState(false);

  const loadInitialData = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [profile, settings] = await Promise.all([
        onboardingApi.getProfile(),
        onboardingApi.getSettings(),
      ]);
      setNickname(profile.nickname || profile.name || "");
      setVoice(profile.voice || settings.voice.tts_voice || "bf_emma");
      setCurrentTtsVoice(settings.voice.tts_voice);
      setCharacter(profile.character === "face" || profile.character === "mark" ? profile.character : "orb");
      setVoiceInputEnabled(profile.voice_input_enabled !== "false");
      setTtsEngine(settings.voice.tts_engine.toLowerCase());
      try {
        setGoogleStatus(await onboardingApi.googleWorkspaceStatus());
        setGoogleError("");
      } catch (statusError) {
        setGoogleStatus(null);
        setGoogleError(
          statusError instanceof Error ? statusError.message : "Could not load Google status."
        );
      }
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Could not load your setup.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadInitialData();
    if (typeof window !== "undefined" && "Notification" in window) {
      setNotificationPermission(Notification.permission);
    } else {
      setNotificationPermission("unsupported");
    }
  }, [loadInitialData]);

  const requestNotifications = async () => {
    if (!("Notification" in window)) {
      setNotificationPermission("unsupported");
      return;
    }
    try {
      const permission = await Notification.requestPermission();
      setNotificationPermission(permission);
    } catch (permissionError) {
      setError(
        permissionError instanceof Error
          ? permissionError.message
          : "Could not request notification permission."
      );
    }
  };

  const connectGoogle = async () => {
    setConnectingGoogle(true);
    setGoogleError("");
    try {
      setGoogleStatus(await onboardingApi.connectGoogleWorkspace());
    } catch (connectError) {
      setGoogleError(
        connectError instanceof Error ? connectError.message : "Google connection failed."
      );
    } finally {
      setConnectingGoogle(false);
    }
  };

  const finish = async () => {
    const cleanNickname = nickname.trim();
    if (!cleanNickname || cleanNickname.length > 30) {
      setError("Enter a nickname between 1 and 30 characters.");
      setStep(0);
      return;
    }
    setSaving(true);
    setError("");
    try {
      const values: Record<(typeof PROFILE_KEYS)[number], string> = {
        nickname: cleanNickname,
        voice,
        character,
        voice_input_enabled: String(voiceInputEnabled),
      };
      await Promise.all(
        PROFILE_KEYS.map((key) => onboardingApi.updateProfile(key, values[key]))
      );
      if (voice !== currentTtsVoice && ttsEngine === "kokoro") {
        await onboardingApi.updateSettings({ TTS_VOICE: voice });
      }
      onComplete({ nickname: cleanNickname, character, voiceInputEnabled });
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Could not save your setup.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-50">
        <p className="text-sm text-slate-500">Preparing your TOBI setup…</p>
      </div>
    );
  }

  if (error && !nickname && !ttsEngine) {
    return (
      <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-50 p-6">
        <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-7 shadow-xl">
          <h1 className="text-xl font-semibold text-slate-900">Could not load setup</h1>
          <p role="alert" className="mt-3 text-sm text-red-700">{error}</p>
          <button onClick={() => void loadInitialData()} className="mt-6 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white">
            Try again
          </button>
        </div>
      </div>
    );
  }

  const stepTitles = ["A little about you", "Make TOBI yours", "Your permissions", "Connect accounts"];

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center overflow-y-auto bg-slate-50 p-4 sm:p-8">
      <section
        aria-labelledby="onboarding-title"
        className="my-auto w-full max-w-2xl rounded-3xl border border-slate-200 bg-white p-6 shadow-xl sm:p-10"
      >
        <div className="mb-8 flex items-center justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-600">TOBI · First-run setup</p>
            <h1 id="onboarding-title" className="mt-2 text-2xl font-semibold text-slate-900">
              {stepTitles[step]}
            </h1>
          </div>
          <span className="text-sm tabular-nums text-slate-500">{step + 1} / {stepTitles.length}</span>
        </div>
        <div className="mb-8 h-1.5 overflow-hidden rounded-full bg-slate-100">
          <div className="h-full rounded-full bg-blue-600 transition-all" style={{ width: `${((step + 1) / stepTitles.length) * 100}%` }} />
        </div>

        {step === 0 && (
          <div>
            <label htmlFor="onboarding-nickname" className="block text-sm font-medium text-slate-800">
              What should TOBI call you?
            </label>
            <input
              id="onboarding-nickname"
              autoComplete="nickname"
              maxLength={30}
              value={nickname}
              onChange={(event) => setNickname(event.target.value)}
              placeholder="Your name or nickname"
              className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
            <p className="mt-2 text-xs text-slate-500">This is saved to your local TOBI profile.</p>
          </div>
        )}

        {step === 1 && (
          <div className="space-y-7">
            <fieldset>
              <legend className="text-sm font-medium text-slate-800">Choose TOBI’s look</legend>
              <div className="mt-3 grid grid-cols-2 gap-3">
                {([
                  ["orb", "Animated orb", "The responsive cinematic orb"],
                  ["face", "Friendly face", "A simple face that reacts while TOBI listens and speaks"],
                  ["mark", "TOBI mark", "A calm, minimal logo"],
                ] as const).map(([value, title, description]) => (
                  <button
                    key={value}
                    type="button"
                    aria-pressed={character === value}
                    onClick={() => setCharacter(value)}
                    className={`rounded-xl border p-4 text-left transition ${character === value ? "border-blue-500 bg-blue-50 ring-1 ring-blue-500" : "border-slate-200 hover:border-slate-300"}`}
                  >
                    <span className="block text-sm font-medium text-slate-900">{title}</span>
                    <span className="mt-1 block text-xs text-slate-500">{description}</span>
                  </button>
                ))}
              </div>
            </fieldset>
            <fieldset>
              <legend className="text-sm font-medium text-slate-800">Spoken voice</legend>
              {ttsEngine === "kokoro" ? (
                <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
                  {VOICES.map((option) => (
                    <button
                      key={option.id}
                      type="button"
                      aria-pressed={voice === option.id}
                      onClick={() => setVoice(option.id)}
                      className={`rounded-xl border px-4 py-3 text-left ${voice === option.id ? "border-blue-500 bg-blue-50" : "border-slate-200 hover:border-slate-300"}`}
                    >
                      <span className="block text-sm font-medium text-slate-900">{option.label}</span>
                      <span className="text-xs text-slate-500">{option.description}</span>
                    </button>
                  ))}
                </div>
              ) : (
                <p className="mt-2 text-sm text-slate-600">
                  Your current speech engine ({ttsEngine || "not reported"}) controls voice selection. Configure Kokoro in Settings to choose a voice here.
                </p>
              )}
            </fieldset>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-5">
            <label className="flex items-start gap-3 rounded-xl border border-slate-200 p-4">
              <input
                type="checkbox"
                checked={voiceInputEnabled}
                onChange={(event) => setVoiceInputEnabled(event.target.checked)}
                className="mt-1 accent-blue-600"
              />
              <span>
                <span className="block text-sm font-medium text-slate-900">Enable voice input</span>
                <span className="mt-1 block text-xs leading-relaxed text-slate-600">Allows microphone recording only when you start it in TOBI. Your browser may ask for access the first time you use it.</span>
              </span>
            </label>
            <div className="rounded-xl border border-slate-200 p-4">
              <p className="text-sm font-medium text-slate-900">Browser notifications</p>
              <p className="mt-1 text-xs leading-relaxed text-slate-600">Optional. Lets TOBI show its own browser notifications; it does not let TOBI read notifications from other phone apps.</p>
              {notificationPermission === "unsupported" ? (
                <p className="mt-3 text-xs text-slate-500">Notifications are not supported in this browser.</p>
              ) : notificationPermission === "granted" ? (
                <p className="mt-3 text-xs font-medium text-green-700">Browser permission granted</p>
              ) : notificationPermission === "denied" ? (
                <p className="mt-3 text-xs text-amber-700">Notifications are blocked in browser settings.</p>
              ) : (
                <button type="button" onClick={() => void requestNotifications()} className="mt-3 rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50">
                  Allow notifications
                </button>
              )}
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="rounded-xl border border-slate-200 p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-sm font-medium text-slate-900">Google Workspace</h2>
                <p className="mt-1 text-xs leading-relaxed text-slate-600">Optional connection for Gmail and Google Calendar read access. Sign-in starts only when you choose to connect.</p>
              </div>
              {googleStatus?.connected ? (
                <span className="shrink-0 rounded-full bg-green-50 px-3 py-1 text-xs font-medium text-green-700">Connected</span>
              ) : null}
            </div>
            {googleStatus?.configured && googleStatus.encrypted_storage_available ? (
              !googleStatus.connected && (
                <button
                  type="button"
                  disabled={connectingGoogle}
                  onClick={() => void connectGoogle()}
                  className="mt-5 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                >
                  {connectingGoogle ? "Complete sign-in in the browser…" : "Connect Google"}
                </button>
              )
            ) : googleStatus ? (
              <p className="mt-4 text-xs text-slate-600">
                {!googleStatus.configured
                  ? "Google OAuth is not configured. You can set it up later in your local environment."
                  : "Encrypted local credential storage is unavailable, so connecting is disabled."}
              </p>
            ) : null}
            {googleError && <p role="alert" className="mt-3 text-xs text-red-700">{googleError}</p>}
            {!googleStatus && googleError && (
              <button type="button" onClick={() => void onboardingApi.googleWorkspaceStatus().then(setGoogleStatus).catch((statusError: unknown) => setGoogleError(statusError instanceof Error ? statusError.message : "Could not load Google status."))} className="mt-3 text-xs font-medium text-blue-700 underline">
                Retry status check
              </button>
            )}
          </div>
        )}

        {error && <p role="alert" className="mt-5 text-sm text-red-700">{error}</p>}

        <div className="mt-9 flex items-center justify-between border-t border-slate-100 pt-5">
          <button
            type="button"
            onClick={() => setStep((current) => Math.max(0, current - 1))}
            disabled={step === 0 || saving}
            className="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50 disabled:invisible"
          >
            Back
          </button>
          {step < stepTitles.length - 1 ? (
            <button
              type="button"
              onClick={() => {
                setError("");
                if (step === 0 && !nickname.trim()) {
                  setError("Enter a nickname to continue.");
                  return;
                }
                setStep((current) => current + 1);
              }}
              className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-700"
            >
              Continue
            </button>
          ) : (
            <button
              type="button"
              onClick={() => void finish()}
              disabled={saving}
              className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
            >
              {saving ? "Saving…" : "Finish setup"}
            </button>
          )}
        </div>
      </section>
    </div>
  );
}
