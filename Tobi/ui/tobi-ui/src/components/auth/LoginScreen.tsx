"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";

interface LoginScreenProps {
  onLogin: (pin: string) => Promise<boolean>;
  error: string | null;
}

export default function LoginScreen({ onLogin, error }: LoginScreenProps) {
  const PIN_LENGTH = 6;
  const [digits, setDigits] = useState<string[]>(Array(PIN_LENGTH).fill(""));
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [shake, setShake] = useState(false);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    inputRefs.current[0]?.focus();
  }, []);

  useEffect(() => {
    if (error) {
      setShake(true);
      setDigits(Array(PIN_LENGTH).fill(""));
      setTimeout(() => {
        setShake(false);
        inputRefs.current[0]?.focus();
      }, 500);
    }
  }, [error]);

  const handleSubmit = useCallback(
    async (pin: string) => {
      setIsSubmitting(true);
      const success = await onLogin(pin);
      if (!success) {
        setIsSubmitting(false);
      }
    },
    [onLogin]
  );

  const handleDigitChange = useCallback(
    (index: number, value: string) => {
      const digit = value.replace(/\D/g, "").slice(-1);
      const newDigits = [...digits];
      newDigits[index] = digit;
      setDigits(newDigits);

      if (digit && index < PIN_LENGTH - 1) {
        inputRefs.current[index + 1]?.focus();
      }

      if (digit && index === PIN_LENGTH - 1) {
        const fullPin = newDigits.join("");
        if (fullPin.length === PIN_LENGTH) {
          handleSubmit(fullPin);
        }
      }
    },
    [digits, handleSubmit]
  );

  const handleKeyDown = useCallback(
    (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Backspace" && !digits[index] && index > 0) {
        inputRefs.current[index - 1]?.focus();
      }
      if (e.key === "Enter") {
        const fullPin = digits.join("");
        if (fullPin.length === PIN_LENGTH) {
          handleSubmit(fullPin);
        }
      }
    },
    [digits, handleSubmit]
  );

  const handlePaste = useCallback(
    (e: React.ClipboardEvent) => {
      e.preventDefault();
      const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, PIN_LENGTH);
      if (pasted.length > 0) {
        const newDigits = Array(PIN_LENGTH).fill("");
        for (let i = 0; i < pasted.length; i++) {
          newDigits[i] = pasted[i];
        }
        setDigits(newDigits);
        const nextEmpty = pasted.length < PIN_LENGTH ? pasted.length : PIN_LENGTH - 1;
        inputRefs.current[nextEmpty]?.focus();
        if (pasted.length === PIN_LENGTH) {
          handleSubmit(pasted);
        }
      }
    },
    [handleSubmit]
  );

  return (
    <div className="h-dvh w-screen flex flex-col items-center justify-center bg-Tobi-bg text-Tobi-text safe-top safe-bottom">
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse at 50% 40%, rgba(71, 217, 180, 0.12) 0%, transparent 60%)",
        }}
      />

      <div className="relative z-10 flex flex-col items-center px-6 max-w-sm w-full">
        <div className="mb-8 text-center">
          <div className="operator-mark mx-auto mb-4 h-14 w-14 rounded-2xl" aria-hidden="true">
            <svg viewBox="0 0 32 32" fill="none">
              <path d="M16 3.5 27 9.8v12.4L16 28.5 5 22.2V9.8L16 3.5Z" stroke="currentColor" strokeWidth="1.5" />
              <path d="M8.5 10.5h15v2.6h-6.1V22h-2.8v-8.9H8.5v-2.6Z" fill="currentColor" />
            </svg>
          </div>
          <h1
            className="text-3xl font-light tracking-[0.3em] mb-2"
            style={{ color: "var(--color-gold-bright)" }}
          >
            TOBI
          </h1>
          <p className="text-sm text-gray-600 font-light">
            Enter your access PIN
          </p>
        </div>

        <div
          className={`flex gap-3 mb-6 ${shake ? "animate-shake" : ""}`}
          onPaste={handlePaste}
        >
          {digits.map((digit, i) => (
            <input
              key={i}
              ref={(el) => { inputRefs.current[i] = el; }}
              type="tel"
              inputMode="numeric"
              pattern="[0-9]*"
              maxLength={1}
              value={digit}
              onChange={(e) => handleDigitChange(i, e.target.value)}
              onKeyDown={(e) => handleKeyDown(i, e)}
              disabled={isSubmitting}
              autoComplete="one-time-code"
              className={`
                w-12 h-14 text-center text-2xl font-mono rounded-lg
                border transition-all duration-200 outline-none
                bg-Tobi-surface-alt backdrop-blur-sm
                ${digit ? "border-Tobi-cyan/60 text-Tobi-text" : "border-Tobi-border text-Tobi-text-muted"}
                focus:border-Tobi-cyan focus:ring-1 focus:ring-Tobi-cyan/30
                disabled:opacity-50
              `}
              style={{ caretColor: "transparent" }}
            />
          ))}
        </div>

        {error && (
          <p className="text-red-700 text-sm mb-4 text-center">{error}</p>
        )}

        {isSubmitting && (
          <div className="flex items-center gap-2 text-Tobi-text-dim text-sm">
            <div className="w-4 h-4 border-2 border-Tobi-cyan/40 border-t-Tobi-cyan rounded-full animate-spin" />
            Verifying...
          </div>
        )}

        <p className="text-xs text-gray-500 text-center mt-8 leading-relaxed">
          The PIN is displayed in the Tobi terminal on startup.
          <br />
          Local connections bypass this screen automatically.
        </p>
      </div>

      <style jsx>{`
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          10%, 30%, 50%, 70%, 90% { transform: translateX(-4px); }
          20%, 40%, 60%, 80% { transform: translateX(4px); }
        }
        .animate-shake {
          animation: shake 0.5s ease-in-out;
        }
      `}</style>
    </div>
  );
}
