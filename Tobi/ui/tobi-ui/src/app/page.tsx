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
  const [characterStyle, setCharacterStyle] = useState<CharacterStyle>("orb");
  const [voiceInputEnabled, setVoiceInputEnabled] = useState(true);
  const [speakingLinger, setSpeakingLinger] = useState(false);
  const [isBrowserMicRecording, setIsBrowserMicRecording] = useState(false);
  const lingerTimerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    try {
      setOnboardingComplete(localStorage.getItem("tobi_onboarding_complete") === "true");
      const savedCharacter = localStorage.getItem("tobi_character");
      setCharacterStyle(savedCharacter === "face" || savedCharacter === "mark" ? savedCharacter : "orb");
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
    (preferences: { nickname: string; character: CharacterStyle; voiceInputEnabled: boolean }) => {
      try {
        localStorage.setItem("tobi_onboarding_complete", "true");
        localStorage.setItem("tobi_user_name", preferences.nickname);
        localStorage.setItem("tobi_character", preferences.character);
        localStorage.setItem("tobi_voice_input_enabled", String(preferences.voiceInputEnabled));
        sessionStorage.removeItem("tobi_greeted_session");
      } catch {
        // Server-side profile persistence remains available if browser storage is disabled.
      }
      setCharacterStyle(preferences.character);
      setVoiceInputEnabled(preferences.voiceInputEnabled);
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
        sessionCost={sessionCost}
      />

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
          disabled={connectionStatus !== "connected"}
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
          disabled={connectionStatus !== "connected"}
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
