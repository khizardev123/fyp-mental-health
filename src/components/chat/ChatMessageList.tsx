"use client";

import { useEffect, useRef } from "react";
import { ChatAvatar } from "./ChatAvatar";

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

type ChatMessageListProps = {
  messages: ChatMessage[];
  streaming?: boolean;
};

export function ChatMessageList({ messages, streaming }: ChatMessageListProps) {
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, streaming]);

  return (
    <div
      className="flex flex-1 flex-col gap-5 overflow-y-auto px-1 py-2"
      role="log"
      aria-live="polite"
      aria-relevant="additions"
    >
      {messages.length === 0 && (
        <div className="card-padded border-dashed surface-secondary py-10 text-center">
          <span
            className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-section text-xl"
            aria-hidden
          >
            💬
          </span>
          <p className="text-sm leading-relaxed text-foreground-secondary">
            Say hello, or share what&apos;s on your mind.
            <br />
            I&apos;m here to listen and respond with care.
          </p>
        </div>
      )}

      {messages.map((m) => (
        <div
          key={m.id}
          className={`flex gap-3 ${m.role === "user" ? "flex-row-reverse" : "flex-row"}`}
        >
          <ChatAvatar variant={m.role === "user" ? "user" : "assistant"} />
          <div
            className={`max-w-[min(100%,28rem)] rounded-2xl px-4 py-3.5 text-sm leading-relaxed shadow-card ${
              m.role === "user"
                ? "rounded-tr-md bg-primary text-white"
                : "rounded-tl-md border border-border bg-card text-foreground"
            }`}
          >
            <p className="whitespace-pre-wrap break-words">{m.content}</p>
          </div>
        </div>
      ))}

      {streaming && (
        <div className="flex gap-3">
          <ChatAvatar variant="assistant" />
          <div className="flex items-center gap-2 rounded-2xl rounded-tl-md border border-border bg-card px-4 py-3.5 text-sm text-foreground-secondary shadow-card">
            <span
              className="inline-flex h-2 w-2 animate-pulse rounded-full bg-primary/50"
              aria-hidden
            />
            Thinking…
          </div>
        </div>
      )}

      <div ref={endRef} />
    </div>
  );
}
