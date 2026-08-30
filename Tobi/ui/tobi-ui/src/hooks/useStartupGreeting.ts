"use client";

/**
 * useStartupGreeting
 *
 * Fires once when the WebSocket connects. Behaviour:
 *
 * First-ever launch (no name stored):
 *   TOBI asks "Before we begin — what should I call you?"
 *   User replies with a name → stored in localStorage → TOBI acknowledges
 *   and gives the full time-aware greeting.
 *
 * Every subsequent launch:
 *   Immediately greets with time-aware salutation using the stored name.
 *
 * The hook injects messages directly via sendMessage so the greeting goes
 * through the full LLM pipeline — TOBI generates the spoken response
 * itself, keeping its personality consistent.
 */

import { useEffect, useRef, useCallback } from "react";

const NAME_KEY = "tobi_user_name";
const GREETED_KEY = "tobi_greeted_session"; // prevents double-fire on HMR

function getStoredName(): string | null {
  try {
    return localStorage.getItem(NAME_KEY);
  } catch {
    return null;
  }
}

function storeName(name: string): void {
  try {
    localStorage.setItem(NAME_KEY, name.trim());
  } catch {}
}

function getTimeOfDay(): "morning" | "afternoon" | "evening" | "night" {
  const h = new Date().getHours();
  if (h >= 5  && h < 12) return "morning";
  if (h >= 12 && h < 17) return "afternoon";
  if (h >= 17 && h < 21) return "evening";
  return "night";
}

function buildGreetingPrompt(name: string): string {
  const tod = getTimeOfDay();
  const todLabel =
    tod === "morning"   ? "Good morning"   :
    tod === "afternoon" ? "Good afternoon" :
    tod === "evening"   ? "Good evening"   : "Hey";

  return (
    `[SYSTEM_STARTUP] The user has just opened TOBI. ` +
    `Greet them as ${name} with "${todLabel}, ${name}." in your first sentence. ` +
    `Keep it short — one warm sentence of greeting, then one sentence asking what they want to tackle today. ` +
    `Sound natural, not robotic. Do not mention that you are an AI or that you are starting up.`
  );
}

function buildFirstTimePrompt(): string {
  return (
    `[SYSTEM_STARTUP_FIRST_TIME] The user has just opened TOBI for the first time. ` +
    `Introduce yourself briefly as TOBI — their personal AI operator — in one sentence. ` +
    `Then ask: "Before we get started — what should I call you?" ` +
    `Keep the tone warm and confident, like a capable assistant meeting someone for the first time. ` +
    `Do not use bullet points or lists.`
  );
}

interface UseStartupGreetingOptions {
  /** Whether the WebSocket is currently connected */
  isConnected: boolean;
  /** Send a message through the normal chat pipeline */
  sendMessage: (text: string) => void;
  /** Whether TOBI is currently processing (prevents firing during boot) */
  isProcessing: boolean;
}

export function useStartupGreeting({
  isConnected,
  sendMessage,
  isProcessing,
}: UseStartupGreetingOptions) {
  const hasFiredRef = useRef(false);
  const awaitingNameRef = useRef(false);

  // Mark the session so HMR reloads don't double-fire
  const sessionKey = typeof window !== "undefined"
    ? sessionStorage.getItem(GREETED_KEY)
    : "1";

  const fire = useCallback(() => {
    if (hasFiredRef.current) return;
    if (typeof window === "undefined") return;
    if (sessionStorage.getItem(GREETED_KEY)) return;

    hasFiredRef.current = true;
    sessionStorage.setItem(GREETED_KEY, "1");

    const name = getStoredName();

    if (name) {
      // Known user — send greeting prompt after a short natural delay
      setTimeout(() => {
        sendMessage(buildGreetingPrompt(name));
      }, 800);
    } else {
      // First time — ask for name
      awaitingNameRef.current = true;
      setTimeout(() => {
        sendMessage(buildFirstTimePrompt());
      }, 800);
    }
  }, [sendMessage]);

  // Fire once when connected and not mid-boot-processing
  useEffect(() => {
    if (isConnected && !isProcessing && !hasFiredRef.current) {
      fire();
    }
  }, [isConnected, isProcessing, fire]);

  /**
   * Call this with every incoming assistant message to detect the
   * name-capture flow. If we're awaiting a name and the user's last
   * message looks like just a name, persist it and send the full greeting.
   *
   * Actually we intercept on the USER side — see handleNameCapture below.
   */
  const handleUserMessage = useCallback(
    (text: string) => {
      if (!awaitingNameRef.current) return;

      const cleaned = text.trim().replace(/['"]/g, "");
      // Accept if it's short (≤ 30 chars) and looks like a name / nickname
      if (cleaned.length > 0 && cleaned.length <= 30 && !/\?|\.{2,}/.test(cleaned)) {
        storeName(cleaned);
        awaitingNameRef.current = false;

        // Send the time-aware greeting now that we have the name
        setTimeout(() => {
          sendMessage(buildGreetingPrompt(cleaned));
        }, 400);
      }
    },
    [sendMessage]
  );

  return {
    handleUserMessage,
    /** Exposed so UI can show a subtle "What should I call you?" hint */
    isAwaitingName: awaitingNameRef,
    /** Utility — clear stored name (for testing / settings reset) */
    clearName: () => {
      try { localStorage.removeItem(NAME_KEY); } catch {}
    },
  };
}
