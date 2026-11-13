"use client";

import { OrbState } from "@/lib/types";

interface HoodedAvatarProps {
  state: OrbState;
}

export default function HoodedAvatar({ state }: HoodedAvatarProps) {
  return (
    <div
      className={`hooded-companion hooded-companion-${state}`}
      role="img"
      aria-label={`TOBI ${state} hooded companion`}
    >
      <svg viewBox="0 0 360 470" aria-hidden="true">
        <defs>
          <linearGradient id="hood-fabric" x1="0" x2="1" y1="0" y2="1">
            <stop offset="0" stopColor="#e9e9ed" />
            <stop offset=".48" stopColor="#b9bbc4" />
            <stop offset="1" stopColor="#858895" />
          </linearGradient>
          <linearGradient id="hood-shadow" x1="0" x2="1" y1="0" y2="1">
            <stop offset="0" stopColor="#777b88" />
            <stop offset=".55" stopColor="#343844" />
            <stop offset="1" stopColor="#171a22" />
          </linearGradient>
          <linearGradient id="visor-glass" x1="0" x2=".95" y1="0" y2="1">
            <stop offset="0" stopColor="#414553" />
            <stop offset=".45" stopColor="#20232c" />
            <stop offset="1" stopColor="#11141b" />
          </linearGradient>
          <linearGradient id="sweatshirt" x1="0" x2="1" y1="0" y2="1">
            <stop offset="0" stopColor="#8b8e98" />
            <stop offset=".5" stopColor="#646874" />
            <stop offset="1" stopColor="#454955" />
          </linearGradient>
          <linearGradient id="sneaker" x1="0" x2="0" y1="0" y2="1">
            <stop offset="0" stopColor="#fffefd" />
            <stop offset="1" stopColor="#d9d9df" />
          </linearGradient>
          <filter id="eye-glow" x="-150%" y="-150%" width="400%" height="400%">
            <feGaussianBlur stdDeviation="5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="character-shadow" x="-30%" y="-20%" width="160%" height="150%">
            <feDropShadow dx="0" dy="12" stdDeviation="10" floodColor="#414653" floodOpacity=".2" />
          </filter>
        </defs>

        <ellipse cx="180" cy="447" rx="112" ry="12" fill="#687080" opacity=".16" />

        <g filter="url(#character-shadow)">
          <path d="M111 344 101 405q-2 17 10 23l24 4 17-11-3-69z" fill="#171a22" />
          <path d="M210 353 214 417q1 14 14 17l24-4q11-5 8-20l-12-66z" fill="#171a22" />
          <path d="M104 408q27 10 51 1l4 15q1 12-10 15l-41-2q-15-3-10-17z" fill="#454955" />
          <path d="M210 413q28 10 52 0l5 14q2 12-10 15l-39-2q-15-3-12-16z" fill="#454955" />
          <path d="M94 427q31-9 68 2l17 16q5 7-5 10H94q-15-3-13-15z" fill="url(#sneaker)" />
          <path d="M204 430q32-8 66 1l18 15q5 8-5 10h-80q-14-2-12-14z" fill="url(#sneaker)" />
          <path d="M86 447q43 8 95 1l-1 8q-1 5-9 6H96q-13-1-12-9zM194 448q44 7 94 0l2 8q-2 6-10 6h-76q-13-1-12-8z" fill="#faf8f7" />
          <path d="M91 438q25-7 54-1M207 440q27-7 55-1" fill="none" stroke="#e5bcb9" strokeWidth="5" strokeLinecap="round" />

          <path d="M115 218q-35 22-48 83l-17 42q-6 15 8 23l16 8q14 6 22-8l22-42 23-81z" fill="url(#sweatshirt)" />
          <path d="M241 218q35 22 48 83l17 42q6 15-8 23l-16 8q-14 6-22-8l-22-42-23-81z" fill="url(#sweatshirt)" />
          <path d="M53 350q18 17 43 14l-9 20q-13 9-31-1-15-10-3-33zM267 364q25 3 43-14 12 23-3 33-18 10-31 1z" fill="#737681" />
          <path d="M54 355q17 13 39 11M270 366q22 2 37-11" fill="none" stroke="#a5a7af" strokeWidth="3" opacity=".7" />

          <path d="M113 220q28-22 67-22t67 22l22 136q-4 23-31 29-58 15-116 0-27-7-31-29z" fill="url(#sweatshirt)" />
          <path d="M116 222q30 10 64 10t64-10" fill="none" stroke="#a4a6ae" strokeWidth="3" opacity=".48" />
          <path d="M143 228v81M216 228v81" stroke="#494d58" strokeWidth="2" opacity=".32" />
          <path d="M153 229q-2 31 7 68M204 229q2 31-7 68" fill="none" stroke="#e9c2b9" strokeWidth="5" strokeLinecap="round" />
          <path d="M158 296l1 20M199 296l1 20" fill="none" stroke="#f5d6cd" strokeWidth="2" strokeLinecap="round" />
          <path d="M139 322q41 16 82 0l11 30q-51 17-104 0z" fill="#737681" opacity=".8" />
          <path d="M140 322q39 13 80 0" fill="none" stroke="#aeb0b6" strokeWidth="2" opacity=".65" />

          <path d="M142 201q-6 14-4 28 11 20 42 21t43-21q2-14-5-28z" fill="#20232c" />
          <path d="M69 104q8-56 58-73 47-17 99-2 57 16 67 72l-4 69q-6 49-46 65-42 17-93 5-45-11-67-49-20-35-14-87z" fill="url(#hood-fabric)" />
          <path d="M92 101q5-42 43-55 41-15 86-3 44 12 53 53l-3 67q-5 39-38 53-34 13-75 3-37-9-53-39-17-29-13-79z" fill="url(#hood-shadow)" />
          <path d="M103 106q5-32 34-43 35-13 73-3 38 10 46 43l-2 57q-4 31-31 42-29 11-64 3-31-8-44-33-14-24-12-66z" fill="url(#visor-glass)" stroke="#0f1218" strokeWidth="2" />
          <path d="M108 101q45-11 138 2" fill="none" stroke="#aeb3c0" strokeWidth="2" opacity=".28" />
          <path d="M81 107q-2 71 30 101M277 107q2 71-30 101" fill="none" stroke="#f8f6f7" strokeWidth="7" opacity=".36" />
          <path d="M73 151q1 48 37 71M287 151q-1 48-37 71" fill="none" stroke="#666a76" strokeWidth="5" opacity=".34" />

          <g filter="url(#eye-glow)">
            <rect x="143" y="126" width="17" height="38" rx="7" fill="#ffb5b4" transform="rotate(10 151.5 145)" />
            <rect x="201" y="138" width="14" height="31" rx="6" fill="#ffb5b4" transform="rotate(10 208 153.5)" />
          </g>
          <path d="M155 186q24 7 49 0" fill="none" stroke="#11141b" strokeWidth="2" opacity=".35" />

          <g fill="#20232c" stroke="#858995" strokeWidth="1.5">
            <path d="M44 394q8-5 14 1l18 14q5 5 1 11l-5 5q-5 4-10 0l-18-14q-6-8 0-17z" />
            <path d="M74 403l9 23q2 5-3 8l-4 2q-5 1-7-5l-8-21zM63 410l7 23q1 6-5 7l-4 1q-5-1-5-6l-5-24zM53 414l4 22q0 6-6 6h-3q-5-2-4-7l-2-22z" />
            <path d="M316 394q-8-5-14 1l-18 14q-5 5-1 11l5 5q5 4 10 0l18-14q6-8 0-17z" />
            <path d="M286 403l-9 23q-2 5 3 8l4 2q5 1 7-5l8-21zM297 410l-7 23q-1 6 5 7l4 1q5-1 5-6l5-24zM307 414l-4 22q0 6 6 6h3q5-2 4-7l2-22z" />
          </g>
          <path d="M51 404l18 14M309 404l-18 14" stroke="#a6a8b1" strokeWidth="2" opacity=".55" />
        </g>
      </svg>
    </div>
  );
}
