"use client";

import { ViewMode, ConnectionStatus } from "@/lib/types";

interface StatusBarProps {
  viewMode: ViewMode;
  onModeChange: (mode: ViewMode) => void;
  connectionStatus: ConnectionStatus;
  sessionCost?: number;
}

const statusLabels: Record<ConnectionStatus, string> = {
  connected: "Online",
  connecting: "Connecting",
  disconnected: "Offline",
  error: "Error",
};

const tabs: { mode: ViewMode; label: string; iconPaths: string[] }[] = [
  {
    mode: "cinematic",
    label: "Voice",
    iconPaths: [
      "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z",
      "M12 6a6 6 0 1 0 0 12 6 6 0 0 0 0-12z",
    ],
  },
  {
    mode: "chat",
    label: "Chat",
    iconPaths: [
      "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z",
    ],
  },
  {
    mode: "reminders",
    label: "Remind",
    iconPaths: [
      "M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9",
      "M13.73 21a2 2 0 0 1-3.46 0",
    ],
  },
  {
    mode: "memory",
    label: "Memory",
    iconPaths: [
      "M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z",
      "M12 6v6l4 2",
    ],
  },
  {
    mode: "dashboard",
    label: "System",
    iconPaths: [
      "M3 3h7v7H3z",
      "M14 3h7v7h-7z",
      "M3 14h7v7H3z",
      "M14 14h7v7h-7z",
    ],
  },
];

export default function StatusBar({
  viewMode,
  onModeChange,
  connectionStatus,
  sessionCost = 0.0,
}: StatusBarProps) {
  return (
    <header className="operator-header w-full flex-shrink-0">
      <div className="operator-header-inner flex items-center justify-between gap-2 px-3 sm:px-7 py-2.5 sm:py-3">
        <div className="operator-brand flex items-center gap-2.5 sm:gap-3">
          <div className="operator-mark" aria-hidden="true">
            <svg viewBox="0 0 32 32" fill="none">
              <path d="M16 3.5 27 9.8v12.4L16 28.5 5 22.2V9.8L16 3.5Z" stroke="currentColor" strokeWidth="1.5" />
              <path d="M8.5 10.5h15v2.6h-6.1V22h-2.8v-8.9H8.5v-2.6Z" fill="currentColor" />
            </svg>
          </div>
          <div className="flex flex-col leading-none">
            <span className="operator-wordmark">TOBI</span>
            <span className="operator-tagline hidden sm:block">PERSONAL OPERATOR</span>
          </div>
        </div>

        <nav className="operator-nav flex min-w-0 items-center p-1 gap-0.5 rounded-2xl" aria-label="Main navigation">
            {tabs.map(({ mode, label, iconPaths }) => {
              const isActive = viewMode === mode;
              return (
                <button
                  key={mode}
                  onClick={() => onModeChange(mode)}
                  className={`operator-nav-item relative flex flex-shrink-0 items-center justify-center gap-1.5 rounded-xl transition-all duration-200 ${isActive ? "is-active" : ""}`}
                  aria-label={label}
                  aria-current={isActive ? "page" : undefined}
                  >
                  <svg
                    width="15"
                    height="15"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.7"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    {iconPaths.map((d, i) => (
                      <path key={i} d={d} />
                    ))}
                  </svg>
                  <span className="operator-nav-label">{label}</span>
                </button>
              );
            })}
        </nav>

        <div className="operator-meta flex items-center gap-2 sm:gap-4">
          <div className="operator-connection flex items-center gap-2" title={statusLabels[connectionStatus]}>
            <div className={`status-dot ${connectionStatus}`} />
            <span className="operator-connection-label">
              {statusLabels[connectionStatus]}
            </span>
          </div>
          <div className="operator-cost hidden sm:flex">
            <span>SESSION</span>
            <strong>${sessionCost.toFixed(4)}</strong>
          </div>
          <div className="operator-cost operator-cost-mobile sm:hidden">
            <strong>${sessionCost.toFixed(2)}</strong>
          </div>
        </div>
      </div>
    </header>
  );
}
