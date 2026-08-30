"use client";

/**
 * usePushNotifications
 *
 * Manages browser Push API subscription and service-worker message routing.
 *
 * Usage:
 *   const { supported, permission, subscribe, unsubscribe } = usePushNotifications();
 *
 * The hook also listens for SW → client messages (SNOOZE_REMINDER,
 * DISMISS_REMINDER, REMINDER_FIRED) and exposes them via `onReminderAction`.
 */

import { useEffect, useCallback, useState } from "react";

export type ReminderAction =
  | { type: "SNOOZE_REMINDER"; reminder_id: number; minutes: number }
  | { type: "DISMISS_REMINDER"; reminder_id: number }
  | { type: "REMINDER_FIRED"; reminder_id: number | null };

interface UsePushNotificationsOptions {
  /** Called when the service worker sends a reminder action. */
  onReminderAction?: (action: ReminderAction) => void;
  /** VAPID public key for Web Push (optional for local-only deployment). */
  vapidPublicKey?: string;
}

export function usePushNotifications({
  onReminderAction,
  vapidPublicKey,
}: UsePushNotificationsOptions = {}) {
  const [supported, setSupported] = useState(false);
  const [permission, setPermission] = useState<NotificationPermission>("default");
  const [subscription, setSubscription] = useState<PushSubscription | null>(null);

  // ── detect support ────────────────────────────────────────────────────────
  useEffect(() => {
    if (typeof window === "undefined") return;
    const ok =
      "serviceWorker" in navigator &&
      "PushManager" in window &&
      "Notification" in window;
    setSupported(ok);
    if (ok) setPermission(Notification.permission);
  }, []);

  // ── listen for SW → client messages ──────────────────────────────────────
  useEffect(() => {
    if (typeof window === "undefined" || !onReminderAction) return;

    const handler = (e: Event) => {
      const { detail } = e as CustomEvent<ReminderAction>;
      if (detail?.type) onReminderAction(detail);
    };

    window.addEventListener("tobi-sw-message", handler);
    return () => window.removeEventListener("tobi-sw-message", handler);
  }, [onReminderAction]);

  // ── request permission + subscribe ───────────────────────────────────────
  const subscribe = useCallback(async (): Promise<PushSubscription | null> => {
    if (!supported) return null;

    const perm = await Notification.requestPermission();
    setPermission(perm);
    if (perm !== "granted") return null;

    try {
      const reg = await navigator.serviceWorker.ready;

      if (vapidPublicKey) {
        const existing = await reg.pushManager.getSubscription();
        if (existing) {
          setSubscription(existing);
          return existing;
        }

        const sub = await reg.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: _urlBase64ToUint8Array(vapidPublicKey),
        });
        setSubscription(sub);
        return sub;
      }

      // No VAPID key: can still show local notifications triggered by
      // the SW message channel, just no server-push capability.
      return null;
    } catch (err) {
      console.warn("[TOBI] Push subscription failed:", err);
      return null;
    }
  }, [supported, vapidPublicKey]);

  // ── unsubscribe ───────────────────────────────────────────────────────────
  const unsubscribe = useCallback(async () => {
    if (!subscription) return;
    await subscription.unsubscribe();
    setSubscription(null);
  }, [subscription]);

interface SwNotificationOptions extends NotificationOptions {
  actions?: Array<{ action: string; title: string; icon?: string }>;
}

  // ── local (in-page) notification helper ──────────────────────────────────
  /** Show a notification directly from the page (no push needed). */
  const showLocal = useCallback(
    async (title: string, body: string, data?: Record<string, unknown>) => {
      if (permission !== "granted") return;
      const reg = await navigator.serviceWorker.ready;
      
      const options: SwNotificationOptions = {
        body,
        icon: "/icon-192.png",
        badge: "/icon-96.png",
        data: data ?? {},
        requireInteraction: Boolean(data?.is_alarm),
        actions: [
          { action: "dismiss", title: "Dismiss" },
          { action: "snooze", title: "Snooze 10 min" },
        ],
      };
      
      reg.showNotification(title, options as NotificationOptions);
    },
    [permission]
  );

  return { supported, permission, subscription, subscribe, unsubscribe, showLocal };
}

// ── utility ───────────────────────────────────────────────────────────────────
function _urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = window.atob(base64);
  const outputArray = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; ++i) {
    outputArray[i] = raw.charCodeAt(i);
  }
  return outputArray;
}
