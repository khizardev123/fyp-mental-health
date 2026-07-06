"use client";



import Link from "next/link";

import { useCallback, useEffect, useMemo, useState } from "react";

import { ChatComposer } from "@/components/chat/ChatComposer";

import { ChatMessageList, type ChatMessage } from "@/components/chat/ChatMessageList";

import { AppHeader } from "@/components/ui/AppHeader";

import { postChatMessage } from "@/lib/chat/postChatMessage";

import type { EmotionContextForChat } from "@/lib/services/chat/types";



type JournalEntryResponse = {

  id: string;

  content: string;

  createdAt: string;

  updatedAt: string;

  emotion: string | null;

  confidence: number | null;

  emotionMessage: string | null;

};



function buildEmotionPayload(

  latest: JournalEntryResponse | null,

): Partial<EmotionContextForChat> | undefined {

  if (!latest) return undefined;

  if (latest.emotion == null && latest.confidence == null && latest.emotionMessage == null) {

    return undefined;

  }

  return {

    emotion: latest.emotion,

    confidence: latest.confidence,

    emotionMessage: latest.emotionMessage,

    journalEntryCreatedAt: latest.createdAt,

  };

}



export default function ChatPage() {

  const [messages, setMessages] = useState<ChatMessage[]>([]);

  const [input, setInput] = useState("");

  const [sending, setSending] = useState(false);

  const [journalState, setJournalState] = useState<"loading" | "ready" | "error">("loading");

  const [journalError, setJournalError] = useState<string | null>(null);

  const [latestEntry, setLatestEntry] = useState<JournalEntryResponse | null>(null);

  const [chatError, setChatError] = useState<string | null>(null);



  const loadJournal = useCallback(async () => {

    setJournalState("loading");

    setJournalError(null);

    try {

      const res = await fetch("/api/journal?limit=1", { credentials: "same-origin" });

      const data = (await res.json()) as { error?: string; entries?: JournalEntryResponse[] };

      if (!res.ok) {

        setJournalState("error");

        setJournalError(data.error ?? "Could not load journal context.");

        setLatestEntry(null);

        return;

      }

      setLatestEntry((data.entries ?? [])[0] ?? null);

      setJournalState("ready");

    } catch {

      setJournalState("error");

      setJournalError("Network error loading journal.");

      setLatestEntry(null);

    }

  }, []);



  useEffect(() => { void loadJournal(); }, [loadJournal]);



  const emotionPayload = useMemo(() => buildEmotionPayload(latestEntry), [latestEntry]);



  async function handleSend() {

    const text = input.trim();

    if (!text || sending) return;

    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: "user", content: text };

    setMessages((prev) => [...prev, userMsg]);

    setInput("");

    setChatError(null);

    setSending(true);

    const result = await postChatMessage({ message: text, emotionContext: emotionPayload });

    setSending(false);

    if (!result.ok) { setChatError(result.error); return; }

    setMessages((prev) => [

      ...prev,

      { id: crypto.randomUUID(), role: "assistant", content: result.data.reply },

    ]);

  }



  const journalBanner =

    journalState === "loading" ? (

      <p className="text-xs text-foreground-secondary">Loading your journal mood…</p>

    ) : journalState === "error" ? (

      <p className="text-xs text-warning">

        {journalError ?? "Journal context unavailable."}{" "}

        <button

          type="button"

          onClick={() => void loadJournal()}

          className="font-medium text-primary underline-offset-2 hover:underline"

        >

          Retry

        </button>

      </p>

    ) : latestEntry?.emotion ? (

      <p className="text-xs text-foreground-secondary">

        From your journal, you seemed to feel{" "}

        <span className="font-medium text-primary">{latestEntry.emotion}</span>

        {typeof latestEntry.confidence === "number" && (

          <span>

            {" "}

            · {(latestEntry.confidence * 100).toFixed(0)}% confidence

          </span>

        )}

      </p>

    ) : (

      <p className="text-xs text-foreground-secondary">

        No journal mood yet — chat still works. Add a{" "}

        <Link

          href="/journal"

          className="font-medium text-primary underline-offset-2 hover:underline"

        >

          journal entry

        </Link>{" "}

        for richer context.

      </p>

    );



  return (

    <div className="flex h-screen flex-col overflow-hidden bg-background text-foreground">

      <AppHeader

        title="Support chat"

        maxWidth="3xl"

        nav={[

          { href: "/dashboard", label: "Dashboard" },

          { href: "/journal", label: "Journal" },

          { href: "/profile", label: "Profile" },

        ]}

      />



      <div className="relative mx-auto flex w-full max-w-3xl flex-1 flex-col overflow-y-auto px-4 pb-0 pt-6">

        <div className="card-padded mb-5 border-l-4 border-l-primary surface-secondary py-5">

          <div className="flex items-start gap-3">

            <span

              className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-section text-lg"

              aria-hidden

            >

              🌸

            </span>

            <div>

              <p className="text-sm leading-relaxed text-foreground">

                I&apos;m here to listen with care. Replies use your recent journal

                mood when available.

              </p>

              <div className="mt-2">{journalBanner}</div>

            </div>

          </div>

        </div>



        {chatError && (

          <div role="alert" className="alert-error mb-4">

            {chatError}

          </div>

        )}



        <ChatMessageList messages={messages} streaming={sending} />

      </div>



      <ChatComposer

        value={input}

        onChange={setInput}

        onSubmit={() => void handleSend()}

        sending={sending}

        className="sticky bottom-0 z-[1]"

      />

    </div>

  );

}

