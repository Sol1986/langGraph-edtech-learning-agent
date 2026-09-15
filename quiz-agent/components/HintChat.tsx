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

// Small chat-style widget for in-quiz hints. Talks to the custom /api/hint
// endpoint (RAG-grounded, see server.py) rather than the CopilotKit agent --
// there's no conversational node in the graph for it to dispatch to, so this
// is a lightweight custom chat UI rather than a wired-up CopilotKit chat
// component (which expects to talk to the agent runtime).
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
    <div className="border dark:border-gray-700 rounded p-3 flex flex-col gap-2 bg-gray-50 dark:bg-gray-900">
      <div className="flex flex-col gap-2">
        {messages.map((m, i) => (
          <div key={i} className={m.role === "user" ? "text-right" : "text-left"}>
            <p className="inline-block rounded px-2 py-1 bg-white dark:bg-gray-800 border dark:border-gray-700 text-sm text-gray-900 dark:text-gray-100">
              {m.text}
            </p>
            {m.sourcePages && m.sourcePages.length > 0 && (
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Referenced from page(s): {m.sourcePages.join(", ")}
              </p>
            )}
          </div>
        ))}
        {isLoading && <p className="text-sm text-gray-500 dark:text-gray-400">Thinking...</p>}
      </div>
      <form onSubmit={handleSend} className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask for a hint or to learn more..."
          className="flex-1 border dark:border-gray-600 rounded px-2 py-1 text-sm"
          disabled={isLoading}
        />
        <button
          type="submit"
          disabled={isLoading || !input.trim()}
          className="rounded bg-gray-700 text-white px-3 py-1 text-sm disabled:opacity-50"
        >
          Ask
        </button>
      </form>
    </div>
  );
}
