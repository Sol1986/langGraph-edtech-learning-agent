"use client";

import { useState } from "react";
import { Streamdown } from "streamdown";

import { resumeThread } from "@/lib/api";
import type { QuizItem } from "@/lib/types";

interface LearningPlanApprovalProps {
  threadId: string;
  topic: string | null;
  learningPlan: string | null;
  onApproved: (quizzes: QuizItem[]) => void;
}

export function LearningPlanApproval({
  threadId,
  topic,
  learningPlan,
  onApproved,
}: LearningPlanApprovalProps) {
  const [feedback, setFeedback] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleApprove() {
    setIsSubmitting(true);
    setError(null);
    try {
      const response = await resumeThread(threadId, feedback.trim() || null);
      onApproved(response.quizzes);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate the quiz.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isSubmitting) {
    return (
      <div className="flex flex-col items-center gap-4 py-24 text-center">
        <span className="h-3 w-3 animate-pulse rounded-full bg-(--color-accent)" />
        <p className="text-[15px] text-(--color-ink-muted)">
          Generating your quiz from the approved plan — this can take a minute.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <div>
        <p className="text-sm font-medium text-(--color-accent)">Lesson plan</p>
        <h2 className="mt-1 text-3xl font-semibold tracking-tight">{topic ?? "Your lesson"}</h2>
      </div>

      {learningPlan && (
        <div className="rounded-3xl border border-(--color-border-soft) bg-(--color-surface) p-8">
          <div className="prose prose-neutral max-w-none prose-headings:font-semibold prose-headings:tracking-tight prose-p:text-(--color-ink-muted) prose-li:text-(--color-ink-muted)">
            <Streamdown mode="static">{learningPlan}</Streamdown>
          </div>
        </div>
      )}

      <label className="flex flex-col gap-2">
        <span className="text-[15px] font-medium">Feedback (optional)</span>
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="e.g. spend more time on section 3, skip the intro concepts…"
          className="min-h-24 resize-none rounded-2xl border border-(--color-border) bg-white p-4 text-[15px] outline-none transition focus:border-(--color-accent) focus:ring-4 focus:ring-(--color-accent)/10"
          rows={3}
        />
      </label>

      <div className="flex items-center gap-4">
        <button
          type="button"
          onClick={handleApprove}
          className="rounded-full bg-(--color-accent) px-6 py-3 text-[15px] font-medium text-white transition hover:bg-(--color-accent-hover) active:scale-[0.98]"
        >
          {feedback.trim() ? "Submit feedback and generate quiz" : "Approve"}
        </button>
        {error && <p className="text-sm text-(--color-danger)">{error}</p>}
      </div>
    </div>
  );
}
