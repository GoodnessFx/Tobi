"use client";

import { OrbState } from "@/lib/types";

interface FaceAvatarProps {
  state: OrbState;
}

export default function FaceAvatar({ state }: FaceAvatarProps) {
  const mouth =
    state === "error" ? "M70 116 Q90 101 110 116" :
    state === "thinking" ? "M77 112 Q90 106 103 112" :
    state === "speaking" ? "M79 108 Q90 130 101 108 Q90 119 79 108" :
    "M72 106 Q90 126 108 106";

  return (
    <div className="flex h-full flex-col items-center justify-center gap-5">
      <svg
        viewBox="0 0 180 180"
        role="img"
        aria-label={`TOBI ${state} face`}
        className={`w-[min(60vw,20rem)] drop-shadow-[0_16px_36px_rgba(14,165,233,0.2)] ${state === "speaking" || state === "listening" ? "animate-pulse" : ""}`}
      >
        <defs>
          <linearGradient id="tobi-face-gradient" x1="0" x2="1" y1="0" y2="1">
            <stop offset="0%" stopColor="#effaff" />
            <stop offset="100%" stopColor="#dbeafe" />
          </linearGradient>
        </defs>
        <circle cx="90" cy="90" r="72" fill="url(#tobi-face-gradient)" stroke="#38bdf8" strokeWidth="3" />
        <path d="M37 67 Q23 69 29 89 M143 67 Q157 69 151 89" fill="none" stroke="#0284c7" strokeWidth="5" strokeLinecap="round" />
        <ellipse cx="65" cy="82" rx="7" ry={state === "thinking" ? 4 : 9} fill="#0f172a" />
        <ellipse cx="115" cy="82" rx="7" ry={state === "thinking" ? 4 : 9} fill="#0f172a" />
        <circle cx="67" cy="79" r="2" fill="white" />
        <circle cx="117" cy="79" r="2" fill="white" />
        <path d={mouth} fill={state === "speaking" ? "#0f172a" : "none"} stroke="#0369a1" strokeWidth="4" strokeLinecap="round" />
        {state === "listening" && (
          <g fill="#38bdf8">
            <circle cx="26" cy="45" r="3" />
            <circle cx="154" cy="45" r="3" />
          </g>
        )}
      </svg>
      <span className="text-xs font-semibold tracking-[0.3em] text-slate-500">TOBI</span>
    </div>
  );
}
