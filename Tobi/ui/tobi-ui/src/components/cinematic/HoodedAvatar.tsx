"use client";

import Image from "next/image";
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
      <Image
        src="/tobi-hooded-character.png"
        alt=""
        width={304}
        height={456}
        priority
        draggable={false}
      />
    </div>
  );
}
