"use client";

import { useState } from "react";

import { requestHint } from "@/lib/api";

interface HintChatProps {
  question: string;
  correctAnswer: string;
}

interface HintMessage {
  role: "user" | "hint";
  text: string;
  sourcePages?: number[];
}

// Small chat-style widget for in-quiz hints, backed by the RAG-grounded
// /api/hint endpoint (see server.py).
export function HintChat({ question, correctAnswer }: HintChatProps) {
  const [messages, setMessages] = useState<HintMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSend(event: React.FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text) return;

    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    setIsLoading(true);
    try {
      const { hint, source_pages } = await requestHint(question, correctAnswer, text);
      setMessages((prev) => [...prev, { role: "hint", text: hint, sourcePages: source_pages }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "hint", text: err instanceof Error ? err.message : "Couldn't fetch a hint." },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-(--color-border-soft) bg-(--color-surface) p-4">
      {messages.length > 0 && (
        <div className="flex flex-col gap-2">
          {messages.map((m, i) => (
            <div key={i} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
              <div className={m.role === "user" ? "max-w-[85%]" : "max-w-[85%]"}>
                <p
                  className={`inline-block rounded-2xl px-3.5 py-2 text-[14px] ${
                    m.role === "user"
                      ? "bg-(--color-accent) text-white"
                      : "border border-(--color-border-soft) bg-white text-(--color-ink)"
                  }`}
                >
                  {m.text}
                </p>
                {m.sourcePages && m.sourcePages.length > 0 && (
                  <p className="mt-1 text-xs text-(--color-ink-muted)">
                    Referenced from page(s): {m.sourcePages.join(", ")}
                  </p>
                )}
              </div>
            </div>
          ))}
          {isLoading && <p className="text-sm text-(--color-ink-muted)">Thinking…</p>}
        </div>
      )}
      <form onSubmit={handleSend} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask for a hint or to learn more…"
          className="flex-1 rounded-full border border-(--color-border) bg-white px-4 py-2 text-[14px] outline-none transition focus:border-(--color-accent) focus:ring-4 focus:ring-(--color-accent)/10"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="rounded-full bg-(--color-ink) px-4 py-2 text-[14px] font-medium text-white transition hover:opacity-90 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
        >
          Ask
        </button>
      </form>
    </div>
  );
}
