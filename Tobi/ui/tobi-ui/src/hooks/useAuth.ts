"use client";

import { useState, useEffect, useCallback, useRef } from "react";

function getApiBaseUrl(): string {
  if (typeof window === "undefined") return "http://localhost:8741";
  const port = window.location.port;
  const hostname = window.location.hostname;
  const isLocal = hostname === "localhost" || hostname === "127.0.0.1";
  if ((!port || port === "443" || port === "80") && !isLocal) {
    return `${window.location.origin}/Tobi-api`;
  }
  return `${window.location.protocol}//${hostname}:8741`;
}

const API_BASE = getApiBaseUrl();

const TOKEN_KEY = "Tobi_auth_token";

function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  try {
    return sessionStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

function storeToken(token: string): void {
  try {
    sessionStorage.setItem(TOKEN_KEY, token);
  } catch {
    // Ignore if sessionStorage unavailable
  }
}

function clearStoredToken(): void {
  try {
    sessionStorage.removeItem(TOKEN_KEY);
  } catch {
    // Ignore
  }
}

export interface AuthState {
  isAuthenticated: boolean;
  isLoading: boolean;
  isLocal: boolean;
  token: string | null;
  loginError: string | null;
  login: (pin: string) => Promise<boolean>;
  logout: () => Promise<void>;
}

export function useAuth(): AuthState {
  // Auth is disabled — no login screen, open access on localhost.
  // The backend still validates tokens for remote connections,
  // but we bypass the gate entirely in the UI.
  const noopLogin = useCallback(async (_pin: string) => true, []);
  const noopLogout = useCallback(async () => {}, []);

  return {
    isAuthenticated: true,
    isLoading: false,
    isLocal: true,
    token: "local",
    loginError: null,
    login: noopLogin,
    logout: noopLogout,
  };
}

