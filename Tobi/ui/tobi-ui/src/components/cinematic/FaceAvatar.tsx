"use client";

import { OrbState } from "@/lib/types";

interface FaceAvatarProps {
  state: OrbState;
}

export default function FaceAvatar({ state }: FaceAvatarProps) {
  const mouth =
    state === "error" ? "M85 145 Q110 127 135 145" :
    state === "thinking" ? "M94 140 Q110 134 126 140" :
    state === "speaking" ? "M96 134 Q110 161 124 134 Q110 147 96 134" :
    "M88 132 Q110 158 132 132";

  return (
    <div className="flex h-full flex-col items-center justify-center gap-5">
      <svg
        viewBox="0 0 220 220"
        role="img"
        aria-label={`TOBI ${state} face`}
        className={`w-[min(60vw,20rem)] drop-shadow-[0_16px_36px_rgba(52,56,49,0.14)] ${state === "speaking" || state === "listening" ? "animate-pulse" : ""}`}
      >
        <defs>
          <linearGradient id="tobi-face-gradient" x1="0" x2="1" y1="0" y2="1">
            <stop offset="0%" stopColor="#71816a" />
            <stop offset="100%" stopColor="#405944" />
          </linearGradient>
          <radialGradient id="tobi-face-light" cx="30%" cy="20%" r="80%">
            <stop offset="0%" stopColor="#fffefa" stopOpacity=".2" />
            <stop offset="100%" stopColor="#fffefa" stopOpacity="0" />
          </radialGradient>
        </defs>
        <circle cx="110" cy="110" r="88" fill="none" stroke="#526b55" strokeOpacity=".16" strokeWidth="1" />
        <circle cx="110" cy="110" r="77" fill="url(#tobi-face-gradient)" stroke="#526b55" strokeOpacity=".6" strokeWidth="2" />
        <circle cx="110" cy="110" r="76" fill="url(#tobi-face-light)" />
        <path d="M47 81 Q31 83 38 107 M173 81 Q189 83 182 107" fill="none" stroke="#526b55" strokeWidth="4" strokeLinecap="round" />
        <ellipse cx="82" cy="101" rx="6" ry={state === "thinking" ? 3 : 8} fill="#f5f4ef" />
        <ellipse cx="138" cy="101" rx="6" ry={state === "thinking" ? 3 : 8} fill="#f5f4ef" />
        <circle cx="84" cy="98" r="1.8" fill="#526b55" />
        <circle cx="140" cy="98" r="1.8" fill="#526b55" />
        <path d={mouth} fill={state === "speaking" ? "#343831" : "none"} stroke="#526b55" strokeWidth="4" strokeLinecap="round" />
        {state === "listening" && (
          <g fill="#9b6b32">
            <circle cx="31" cy="54" r="3" />
            <circle cx="189" cy="54" r="3" />
          </g>
        )}
      </svg>
      <span className="text-xs font-semibold tracking-[0.16em] text-Tobi-cyan/70">TOBI</span>
    </div>
  );
}
