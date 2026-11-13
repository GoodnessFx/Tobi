"use client";

import { useCallback, useEffect, useState } from "react";
import {
  GoogleWorkspaceStatus,
  onboardingApi,
} from "@/hooks/useTobiApi";
import { CharacterStyle } from "@/lib/types";

interface OnboardingPreferences {
  nickname: string;
  character: CharacterStyle;
  voiceInputEnabled: boolean;
  serverProfileSaved: boolean;
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
  const [character, setCharacter] = useState<CharacterStyle>("hooded");
  const [voiceInputEnabled, setVoiceInputEnabled] = useState(true);
  const [notificationPermission, setNotificationPermission] =
    useState<NotificationPermission | "unsupported">("default");
  const [ttsEngine, setTtsEngine] = useState("");
  const [currentTtsVoice, setCurrentTtsVoice] = useState("");
  const [googleStatus, setGoogleStatus] = useState<GoogleWorkspaceStatus | null>(null);
  const [googleError, setGoogleError] = useState("");
  const [setupWarning, setSetupWarning] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [canContinueLocally, setCanContinueLocally] = useState(false);
  const [connectingGoogle, setConnectingGoogle] = useState(false);

  const loadInitialData = useCallback(async () => {
    setLoading(true);
    setError("");
    setSetupWarning("");
    const [profileResult, settingsResult] = await Promise.allSettled([
      onboardingApi.getProfile(),
      onboardingApi.getSettings(),
    ]);
    const warnings: string[] = [];

    if (profileResult.status === "fulfilled") {
      const profile = profileResult.value;
      setNickname(profile.nickname || profile.name || "");
      setCharacter(profile.character === "face" || profile.character === "mark" ? profile.character : "hooded");
      setVoiceInputEnabled(profile.voice_input_enabled !== "false");
    } else {
      warnings.push("Saved profile settings could not be loaded.");
    }

    if (settingsResult.status === "fulfilled") {
      const settings = settingsResult.value;
      setVoice(
        profileResult.status === "fulfilled"
          ? profileResult.value.voice || settings.voice.tts_voice || "bf_emma"
          : settings.voice.tts_voice || "bf_emma"
      );
      setCurrentTtsVoice(settings.voice.tts_voice);
      setTtsEngine(settings.voice.tts_engine.toLowerCase());
    } else {
      warnings.push("Server settings are unavailable; you can still finish setup on this device.");
      setVoice("bf_emma");
      setCurrentTtsVoice("");
      setTtsEngine("");
    }

    setSetupWarning(warnings.join(" "));
    setLoading(false);

    void onboardingApi.googleWorkspaceStatus()
      .then((google) => {
        setGoogleStatus(google);
        setGoogleError("");
      })
      .catch((statusError: unknown) => {
        setGoogleStatus(null);
        setGoogleError(
          statusError instanceof Error ? statusError.message : "Could not load Google status."
        );
      });
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
    if (cleanNickname.length > 30) {
      setError("Keep your name to 30 characters or fewer.");
      setStep(0);
      return;
    }
    setSaving(true);
    setError("");
    setCanContinueLocally(false);
    try {
      const values = PROFILE_KEYS
        .filter((key) => key !== "nickname" || cleanNickname.length > 0)
        .map((key) => ({
          key,
          value: key === "nickname"
            ? cleanNickname
            : key === "voice"
              ? voice
              : key === "character"
                ? character
                : String(voiceInputEnabled),
        }));
      await Promise.all(
        values.map(({ key, value }) => onboardingApi.updateProfile(key, value))
      );
      if (voice !== currentTtsVoice && ttsEngine === "kokoro") {
        await onboardingApi.updateSettings({ TTS_VOICE: voice });
      }
      onComplete({ nickname: cleanNickname, character, voiceInputEnabled, serverProfileSaved: true });
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "Could not save your setup.");
      setCanContinueLocally(true);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-50">
        <p className="text-sm text-slate-500">Getting your setup ready…</p>
      </div>
    );
  }

  const stepTitles = ["About you", "Make TOBI yours", "Optional connections"];

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center overflow-y-auto bg-slate-50 p-4 sm:p-8">
      <section
        aria-labelledby="onboarding-title"
        className="my-auto w-full max-w-2xl rounded-3xl border border-slate-200 bg-white p-6 shadow-xl sm:p-10"
      >
        <div className="mb-8 flex items-center justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.1em] text-blue-600">TOBI · First-run setup</p>
            <h1 id="onboarding-title" className="mt-2 text-2xl font-semibold text-slate-900">
              {stepTitles[step]}
            </h1>
          </div>
          <span className="text-sm tabular-nums text-slate-500">{step + 1} / {stepTitles.length}</span>
        </div>
        <div className="mb-8 h-1.5 overflow-hidden rounded-full bg-slate-100">
          <div className="h-full rounded-full bg-blue-600 transition-all" style={{ width: `${((step + 1) / stepTitles.length) * 100}%` }} />
        </div>

        {setupWarning && (
          <p className="mb-6 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
            {setupWarning}
          </p>
        )}

        {step === 0 && (
          <div>
            <label htmlFor="onboarding-nickname" className="block text-sm font-medium text-slate-800">
              What should TOBI call you? <span className="font-normal text-slate-500">Optional</span>
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
            <p className="mt-2 text-xs text-slate-500">You can leave this blank and add a name later.</p>
          </div>
        )}

        {step === 1 && (
          <div className="space-y-7">
            <fieldset>
              <legend className="text-sm font-medium text-slate-800">Choose TOBI’s look</legend>
              <div className="mt-3 grid grid-cols-2 gap-3">
                {([
                  ["hooded", "Hooded companion", "A soft, animated robot inspired by the TOBI look"],
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
                  {ttsEngine
                    ? `Your current speech engine (${ttsEngine}) controls voice selection. Configure Kokoro in Settings to choose a voice here.`
                    : "Voice selection is available in Settings when the server is connected."}
                </p>
              )}
            </fieldset>
          </div>
        )}

        {step === 1 && (
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
                <span className="mt-1 block text-xs leading-relaxed text-slate-600">TOBI only uses your microphone when you start recording. Your browser may ask for permission the first time.</span>
              </span>
            </label>
            <div className="flex items-start gap-3 rounded-xl border border-slate-200 p-4">
              <span className="min-w-0 flex-1">
                <span className="block text-sm font-medium text-slate-900">Browser notifications</span>
                <span className="mt-1 block text-xs leading-relaxed text-slate-600">Optional. This only allows TOBI’s own reminders; it cannot read notifications from other apps.</span>
                {notificationPermission === "unsupported" ? (
                  <span className="mt-3 block text-xs text-slate-500">Not supported in this browser.</span>
                ) : notificationPermission === "granted" ? (
                  <span className="mt-3 block text-xs font-medium text-green-700">Permission granted</span>
                ) : notificationPermission === "denied" ? (
                  <span className="mt-3 block text-xs text-amber-700">Blocked in browser settings.</span>
                ) : (
                  <button type="button" onClick={() => void requestNotifications()} className="mt-3 rounded-lg border border-slate-300 px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50">
                    Allow notifications
                  </button>
                )}
              </span>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="rounded-xl border border-slate-200 p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-sm font-medium text-slate-900">Google Workspace</h2>
                <p className="mt-1 text-xs leading-relaxed text-slate-600">Connect Gmail and Google Calendar if you want to. You can do this later in settings.</p>
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
        {canContinueLocally && (
          <div className="mt-5 rounded-xl border border-amber-200 bg-amber-50 p-4">
            <p className="text-sm text-amber-900">
              Your server did not save these preferences. You can still try the app on this device; chat and server features need TOBI running.
            </p>
            <button
              type="button"
              onClick={() => onComplete({ nickname: nickname.trim(), character, voiceInputEnabled, serverProfileSaved: false })}
              className="mt-3 rounded-lg border border-amber-800/20 px-4 py-2 text-sm font-medium text-amber-950 hover:bg-amber-100"
            >
              Continue on this device
            </button>
          </div>
        )}

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
                if (step === 0 && nickname.trim().length > 30) {
                  setError("Keep your name to 30 characters or fewer.");
                  return;
                }
                setStep((current) => current + 1);
              }}
              className="rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-700"
            >
              Next
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
