"use client";

import { useState, useCallback, useMemo, useEffect, useRef } from "react";
import { CharacterStyle, ViewMode, OrbState } from "@/lib/types";
import { useTobiWebSocket } from "@/hooks/useTobiWebSocket";
import { useServerStatus } from "@/hooks/useServerStatus";
import { useStartupGreeting } from "@/hooks/useStartupGreeting";
import StatusBar from "@/components/shared/StatusBar";
import ProactiveToast from "@/components/shared/ProactiveToast";
import PlanProgress from "@/components/shared/PlanProgress";
import CinematicView from "@/components/cinematic/CinematicView";
import ChatView from "@/components/chat/ChatView";
import DashboardView from "@/components/dashboard/DashboardView";
import RemindersPanel from "@/components/reminders/RemindersPanel";
import MemoryPanel from "@/components/memory/MemoryPanel";
import { SettingsPanel } from "@/components/settings/SettingsPanel";
import OnboardingWizard from "@/components/onboarding/OnboardingWizard";

const SPEAKING_LINGER_MS = 1800;

export default function Page() {
  const [viewMode, setViewMode] = useState<ViewMode>("cinematic");
  const [onboardingComplete, setOnboardingComplete] = useState<boolean | null>(null);
  const [characterStyle, setCharacterStyle] = useState<CharacterStyle>("hooded");
  const [voiceInputEnabled, setVoiceInputEnabled] = useState(true);
  const [setupSavedLocally, setSetupSavedLocally] = useState(false);
  const [speakingLinger, setSpeakingLinger] = useState(false);
  const [isBrowserMicRecording, setIsBrowserMicRecording] = useState(false);
  const lingerTimerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    try {
      setOnboardingComplete(localStorage.getItem("tobi_onboarding_complete") === "true");
      setSetupSavedLocally(localStorage.getItem("tobi_setup_local_only") === "true");
      const savedCharacter = localStorage.getItem("tobi_character");
      const characterVersion = localStorage.getItem("tobi_character_version");
      const character =
        savedCharacter === "face" || savedCharacter === "mark" ||
        (savedCharacter === "orb" && characterVersion === "2")
          ? savedCharacter
          : "hooded";
      setCharacterStyle(character);
      localStorage.setItem("tobi_character", character);
      localStorage.setItem("tobi_character_version", "2");
      setVoiceInputEnabled(localStorage.getItem("tobi_voice_input_enabled") !== "false");
    } catch {
      setOnboardingComplete(false);
    }
  }, []);

  const {
    status: connectionStatus,
    messages,
    costSummary,
    sendMessage,
    clearMessages,
    isProcessing,
    isStreaming,
    isVoiceSpeaking,
    currentAmplitude,
    sendBrowserMicState,
    suggestions,
    dismissSuggestion,
    activePlan,
  } = useTobiWebSocket(null);

  const { serverStatus } = useServerStatus(null);

  // ── Startup greeting — fires once on connect ─────────────────────────
  const { handleUserMessage: greetingIntercept } = useStartupGreeting({
    enabled: onboardingComplete === true,
    isConnected: connectionStatus === "connected",
    sendMessage,
    isProcessing,
  });

  // ── Linger animation after voice/stream ends ─────────────────────────
  const prevStreamingRef = useRef(false);
  const prevVoiceSpeakingRef = useRef(false);
  useEffect(() => {
    const wasStreaming = prevStreamingRef.current;
    const wasVoice = prevVoiceSpeakingRef.current;
    prevStreamingRef.current = isStreaming;
    prevVoiceSpeakingRef.current = isVoiceSpeaking;

    if ((wasStreaming && !isStreaming) || (wasVoice && !isVoiceSpeaking)) {
      if (!isStreaming && !isVoiceSpeaking) {
        setSpeakingLinger(true);
        if (lingerTimerRef.current) clearTimeout(lingerTimerRef.current);
        lingerTimerRef.current = setTimeout(() => setSpeakingLinger(false), SPEAKING_LINGER_MS);
      }
    }
    if (isProcessing) {
      setSpeakingLinger(false);
      if (lingerTimerRef.current) { clearTimeout(lingerTimerRef.current); lingerTimerRef.current = null; }
    }
  }, [isStreaming, isVoiceSpeaking, isProcessing]);

  useEffect(() => () => { if (lingerTimerRef.current) clearTimeout(lingerTimerRef.current); }, []);

  // ── Handlers ─────────────────────────────────────────────────────────
  const handleBrowserMicState = useCallback(
    (recording: boolean) => { setIsBrowserMicRecording(recording); sendBrowserMicState(recording); },
    [sendBrowserMicState]
  );

  // Intercept user messages for name-capture during first-time flow
  const handleChatSubmit = useCallback(
    (message: string) => { greetingIntercept(message); sendMessage(message); },
    [sendMessage, greetingIntercept]
  );

  const handleModeChange = useCallback((mode: ViewMode) => setViewMode(mode), []);

  const handleOnboardingComplete = useCallback(
    (preferences: {
      nickname: string;
      character: CharacterStyle;
      voiceInputEnabled: boolean;
      serverProfileSaved: boolean;
    }) => {
      try {
        localStorage.setItem("tobi_onboarding_complete", "true");
        if (preferences.nickname) {
          localStorage.setItem("tobi_user_name", preferences.nickname);
        } else {
          localStorage.removeItem("tobi_user_name");
        }
        localStorage.setItem("tobi_character", preferences.character);
        localStorage.setItem("tobi_character_version", "2");
        localStorage.setItem("tobi_voice_input_enabled", String(preferences.voiceInputEnabled));
        localStorage.setItem("tobi_setup_local_only", String(!preferences.serverProfileSaved));
        sessionStorage.removeItem("tobi_greeted_session");
      } catch {
        // The app can still be used for this session if browser storage is unavailable.
      }
      setCharacterStyle(preferences.character);
      setVoiceInputEnabled(preferences.voiceInputEnabled);
      setSetupSavedLocally(!preferences.serverProfileSaved);
      setOnboardingComplete(true);
    },
    []
  );

  const orbState: OrbState = useMemo(() => {
    if (connectionStatus === "error") return "error";
    if (isProcessing)          return "thinking";
    if (isStreaming)           return "speaking";
    if (isVoiceSpeaking)       return "speaking";
    if (speakingLinger)        return "speaking";
    if (isBrowserMicRecording) return "listening";
    return "idle";
  }, [connectionStatus, isProcessing, isStreaming, isVoiceSpeaking, speakingLinger, isBrowserMicRecording]);

  const sessionCost = costSummary?.sessionCostUsd ?? 0;
  const isActive = isProcessing || isStreaming;
  const aiBackendUnavailable = serverStatus?.activeBackend === "none";
  const chatDisabled = connectionStatus !== "connected" || aiBackendUnavailable;

  // ── Render ────────────────────────────────────────────────────────────
  if (onboardingComplete === null) {
    return <div className="h-dvh w-screen bg-slate-50" aria-busy="true" />;
  }

  return (
    <div
      className="h-dvh w-screen flex flex-col overflow-hidden safe-top safe-bottom"
      style={{ background: "var(--tobi-bg)" }}
    >
      <StatusBar
        viewMode={viewMode}
        onModeChange={handleModeChange}
        connectionStatus={connectionStatus}
        aiBackendUnavailable={aiBackendUnavailable}
        sessionCost={sessionCost}
      />

      {setupSavedLocally && (
        <div className="mx-3 mt-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950 sm:mx-7">
          Setup is saved in this browser only. Start the TOBI server to test chat and sync your profile.
        </div>
      )}
      {aiBackendUnavailable && (
        <div className="mx-3 mt-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950 sm:mx-7" role="status">
          The server is connected, but no AI provider passed its startup check. Use Settings to test an Anthropic key, then configure it in the server&apos;s .env and restart, or start Ollama with the configured model.
        </div>
      )}

      {/* Cinematic orb view — always mounted, hidden when inactive */}
      <div
        className="flex-1 flex flex-col"
        style={{ display: viewMode === "cinematic" ? "flex" : "none" }}
      >
        <CinematicView
          messages={messages}
          orbState={orbState}
          isProcessing={isActive}
          currentAmplitude={currentAmplitude}
          onSendMessage={handleChatSubmit}
          onOpenChat={() => setViewMode("chat")}
          disabled={chatDisabled}
          onBrowserMicState={handleBrowserMicState}
          authToken={null}
          characterStyle={characterStyle}
          voiceInputEnabled={voiceInputEnabled}
        />
      </div>

      {viewMode === "chat" && (
        <ChatView
          messages={messages}
          isProcessing={isActive}
          onSendMessage={handleChatSubmit}
          onClearConversation={clearMessages}
          disabled={chatDisabled}
          onBrowserMicState={handleBrowserMicState}
          authToken={null}
          voiceInputEnabled={voiceInputEnabled}
        />
      )}

      {viewMode === "dashboard" && (
        <DashboardView
          messages={messages}
          costSummary={costSummary}
          serverStatus={serverStatus}
          isProcessing={isActive}
          onClearConversation={clearMessages}
        />
      )}

      {viewMode === "reminders" && (
        <div className="flex-1 overflow-hidden">
          <RemindersPanel />
        </div>
      )}

      {viewMode === "memory" && (
        <div className="flex-1 overflow-hidden">
          <MemoryPanel token={null} />
        </div>
      )}

      <ProactiveToast suggestions={suggestions} onDismiss={dismissSuggestion} />
      <PlanProgress plan={activePlan} />
      <SettingsPanel />
      {!onboardingComplete && <OnboardingWizard onComplete={handleOnboardingComplete} />}
    </div>
  );
}
