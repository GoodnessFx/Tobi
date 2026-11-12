"use client";

import React, { useState, useEffect } from "react";
import PwaInstallCard from "@/components/settings/PwaInstallCard";
import { settingsApi, TobiSettings, TobiSystemStatus } from "@/hooks/useTobiApi";

type Step = "api_keys" | "models" | "voice" | "costs";

export function SettingsPanel() {
  const [isOpen, setIsOpen] = useState(false);
  const [currentStep, setCurrentStep] = useState<Step>("api_keys");
  const [settings, setSettings] = useState<TobiSettings | null>(null);
  const [status, setStatus] = useState<TobiSystemStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [apiKey, setApiKey] = useState("");
  const [ollamaUrl, setOllamaUrl] = useState("");
  const [apiKeyValid, setApiKeyValid] = useState<boolean | null>(null);
  const [ollamaValid, setOllamaValid] = useState<boolean | null>(null);

  // Load settings on mount
  useEffect(() => {
    if (isOpen) {
      loadSettings();
      loadStatus();
    }
  }, [isOpen]);

  async function loadSettings() {
    try {
      const currentSettings = await settingsApi.get();
      setSettings(currentSettings);
      setOllamaUrl(currentSettings.integrations.ollama_url);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load settings");
      console.error(err);
    }
  }

  async function loadStatus() {
    try {
      setStatus(await settingsApi.status());
    } catch (err) {
      console.error("Failed to load status:", err);
    }
  }

  async function testApiKey() {
    if (!apiKey) {
      setError("Please enter an API key");
      return;
    }

    setLoading(true);
    try {
      const result = await settingsApi.testAnthropic(apiKey);

      if (result.valid) {
        setApiKeyValid(true);
        setError(null);
      } else {
        setApiKeyValid(false);
        setError(result.error || "API key is invalid");
      }
    } catch (err) {
      setApiKeyValid(false);
      setError("Failed to test API key");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function testOllama() {
    if (!ollamaUrl) {
      setError("Please enter Ollama URL");
      return;
    }

    setLoading(true);
    try {
      const result = await settingsApi.testOllama();

      if (result.valid) {
        setOllamaValid(true);
        setError(null);
      } else {
        setOllamaValid(false);
        setError(result.error || "Ollama is not reachable");
      }
    } catch (err) {
      setOllamaValid(false);
      setError("Failed to test Ollama");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  async function saveSettings(updates: Record<string, string | number>) {
    setLoading(true);
    try {
      const result = await settingsApi.update(updates);
      if (result.success) {
        setError(null);
        await loadSettings();
      } else {
        setError(result.error || "Failed to save settings");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save settings");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  const isSmallScreen = typeof window !== "undefined" && window.innerWidth < 768;

  return (
    <>
      {/* Settings Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="operator-settings-button fixed bottom-5 right-5 sm:bottom-7 sm:right-7 w-12 h-12 rounded-2xl transition-all duration-200 flex items-center justify-center z-40 backdrop-blur-sm"
        title="Settings"
        aria-label={isOpen ? "Close settings" : "Settings"}
      >
        <svg
          className="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
          />
        </svg>
      </button>

      {/* Panel Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Sliding Panel */}
      <div
        className={`fixed top-0 right-0 h-full w-full md:w-96 bg-Tobi-surface border-l border-Tobi-border shadow-2xl z-50 transform transition-transform duration-300 ease-out overflow-y-auto ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        {/* Panel Header */}
        <div className="sticky top-0 bg-Tobi-surface/95 backdrop-blur-md border-b border-Tobi-border p-4 flex justify-between items-center">
          <h2 className="text-xl font-bold text-Tobi-text">Tobi Settings</h2>
          <button
            onClick={() => setIsOpen(false)}
            className="text-slate-500 hover:text-slate-900 transition"
          >
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mx-4 mt-4 p-3 bg-red-50 border border-red-200 rounded text-red-800 text-sm">
            {error}
          </div>
        )}

        {/* Content */}
        <div className="p-4 space-y-6">
          <PwaInstallCard />

          {/* Step Indicator */}
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentStep("api_keys")}
              className={`flex-1 py-2 px-3 rounded text-xs font-semibold transition ${
                currentStep === "api_keys"
                  ? "bg-blue-600 text-white"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
            >
              API
            </button>
            <button
              onClick={() => setCurrentStep("models")}
              className={`flex-1 py-2 px-3 rounded text-xs font-semibold transition ${
                currentStep === "models"
                  ? "bg-blue-600 text-white"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
            >
              Models
            </button>
            <button
              onClick={() => setCurrentStep("voice")}
              className={`flex-1 py-2 px-3 rounded text-xs font-semibold transition ${
                currentStep === "voice"
                  ? "bg-blue-600 text-white"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
            >
              Voice
            </button>
            <button
              onClick={() => setCurrentStep("costs")}
              className={`flex-1 py-2 px-3 rounded text-xs font-semibold transition ${
                currentStep === "costs"
                  ? "bg-blue-600 text-white"
                  : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
            >
              Costs
            </button>
          </div>

          {/* Step 1: API Keys */}
          {currentStep === "api_keys" && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-slate-800 mb-2">
                  Anthropic API key
                </label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="sk-..."
                  autoComplete="off"
                  className="w-full px-3 py-2 bg-white border border-slate-300 rounded text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500 transition"
                />
                <p className="mt-2 text-xs text-slate-500">
                  Test only; this key is not saved. Configure it on the TOBI server to use Claude.
                </p>
                <button
                  onClick={testApiKey}
                  disabled={loading}
                  className="mt-2 w-full py-2 px-3 bg-blue-600 hover:bg-blue-700 text-white rounded font-semibold transition disabled:opacity-50"
                >
                  {loading ? "Testing..." : "Test API"}
                </button>
                {apiKeyValid === true && (
                  <p className="mt-2 text-green-700 text-sm">API key is valid</p>
                )}
                {apiKeyValid === false && (
                  <p className="mt-2 text-red-700 text-sm">API key is invalid</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-800 mb-2">
                  Configured Ollama URL
                </label>
                <input
                  type="text"
                  value={ollamaUrl}
                  readOnly
                  placeholder="http://localhost:11434"
                  className="w-full px-3 py-2 bg-white border border-slate-300 rounded text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500 transition"
                />
                <p className="mt-2 text-xs text-slate-500">
                  To test a different server, update OLLAMA_BASE_URL in the TOBI server configuration.
                </p>
                <button
                  onClick={testOllama}
                  disabled={loading}
                  className="mt-2 w-full py-2 px-3 bg-blue-600 hover:bg-blue-700 text-white rounded font-semibold transition disabled:opacity-50"
                >
                  {loading ? "Testing..." : "Test Ollama"}
                </button>
                {ollamaValid === true && (
                  <p className="mt-2 text-green-700 text-sm">Ollama is reachable</p>
                )}
                {ollamaValid === false && (
                  <p className="mt-2 text-red-700 text-sm">Ollama is not reachable</p>
                )}
              </div>

              {/* Status Indicators */}
              {status && (
                <div className="mt-6 p-3 bg-slate-50 border border-slate-200 rounded space-y-2">
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-2 h-2 rounded-full ${
                        status.anthropic ? "bg-green-500" : "bg-red-500"
                      }`}
                    />
                    <span className="text-sm text-slate-700">
                      Anthropic: {status.anthropic ? "Connected" : "Disconnected"}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-2 h-2 rounded-full ${
                        status.ollama ? "bg-green-500" : "bg-red-500"
                      }`}
                    />
                    <span className="text-sm text-slate-700">
                      Ollama: {status.ollama ? "Connected" : "Disconnected"}
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 2: Models */}
          {currentStep === "models" && settings && (
            <div className="space-y-3">
              <div>
                <label className="text-sm font-semibold text-slate-800">
                  Fast Model
                </label>
                <p className="text-xs text-slate-600">{settings.models.fast}</p>
              </div>
              <div>
                <label className="text-sm font-semibold text-slate-800">
                  Brain Model
                </label>
                <p className="text-xs text-slate-600">{settings.models.brain}</p>
              </div>
              <div>
                <label className="text-sm font-semibold text-slate-800">
                  Deep Model
                </label>
                <p className="text-xs text-slate-600">{settings.models.deep}</p>
              </div>
              <div>
                <label className="text-sm font-semibold text-slate-300">
                  Default Tier
                </label>
                <select
                  defaultValue={settings.models.default}
                  onChange={(e) => saveSettings({ CLAUDE_DEFAULT_TIER: e.target.value })}
                  className="mt-1 w-full px-3 py-2 bg-white border border-slate-300 rounded text-slate-900 focus:outline-none focus:border-blue-500"
                >
                  <option value="fast">Fast (Haiku)</option>
                  <option value="brain">Brain (Sonnet)</option>
                  <option value="deep">Deep (Opus)</option>
                </select>
              </div>
            </div>
          )}

          {/* Step 3: Voice */}
          {currentStep === "voice" && settings && (
            <div className="space-y-3">
              <div>
                <label className="text-sm font-semibold text-slate-800">
                  TTS Engine
                </label>
                <p className="text-xs text-slate-600">{settings.voice.tts_engine}</p>
              </div>
              <div>
                <label className="text-sm font-semibold text-slate-800">
                  Voice
                </label>
                <p className="text-xs text-slate-600">{settings.voice.tts_voice}</p>
              </div>
              <div>
                <label className="text-sm font-semibold text-slate-800">
                  Speech Speed
                </label>
                <input
                  type="number"
                  min="0.5"
                  max="2.0"
                  step="0.05"
                  defaultValue={settings.voice.tts_speed}
                  onChange={(e) => saveSettings({ TTS_SPEED: parseFloat(e.target.value) })}
                  className="mt-1 w-full px-3 py-2 bg-white border border-slate-300 rounded text-slate-900 focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="text-sm font-semibold text-slate-800">
                  STT Engine
                </label>
                <p className="text-xs text-slate-600">{settings.voice.stt_engine}</p>
              </div>
            </div>
          )}

          {/* Step 4: Costs */}
          {currentStep === "costs" && settings && (
            <div className="space-y-3">
              <div>
                <label className="text-sm font-semibold text-slate-800">
                  Daily Alert Threshold (USD)
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  defaultValue={settings.costs.daily_alert_usd}
                  onChange={(e) => saveSettings({ COST_DAILY_ALERT: parseFloat(e.target.value) })}
                  className="mt-1 w-full px-3 py-2 bg-white border border-slate-300 rounded text-slate-900 focus:outline-none focus:border-blue-500"
                />
              </div>
              <div>
                <label className="text-sm font-semibold text-slate-800">
                  Monthly Alert Threshold (USD)
                </label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  defaultValue={settings.costs.monthly_alert_usd}
                  onChange={(e) => saveSettings({ COST_MONTHLY_ALERT: parseFloat(e.target.value) })}
                  className="mt-1 w-full px-3 py-2 bg-white border border-slate-300 rounded text-slate-900 focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>
          )}

          {/* System Info */}
          {status && (
            <div className="mt-6 p-3 bg-slate-50 rounded border border-slate-200 space-y-2 text-xs text-slate-600">
              <div>Memory entries: {status.memory_count}</div>
              <div>Uptime: {Math.floor(status.uptime_seconds / 60)}m</div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
