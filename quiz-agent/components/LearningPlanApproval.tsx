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
    return <p>Generating your quiz from the approved plan... this can take a minute.</p>;
  }

  return (
    <div className="flex flex-col gap-4 max-w-2xl">
      <h2 className="text-xl font-semibold">{topic ?? "Lesson plan"}</h2>
      {learningPlan && (
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <Streamdown mode="static">{learningPlan}</Streamdown>
        </div>
      )}
      <label className="flex flex-col gap-2">
        <span className="font-medium">Feedback (optional)</span>
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="e.g. spend more time on section 3, skip the intro concepts..."
          className="border dark:border-gray-600 rounded p-2"
          rows={3}
        />
      </label>
      <button
        type="button"
        onClick={handleApprove}
        className="rounded bg-blue-600 text-white px-4 py-2 self-start"
      >
        {feedback.trim() ? "Submit feedback and generate quiz" : "Approve"}
      </button>
      {error && <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>}
    </div>
  );
}
