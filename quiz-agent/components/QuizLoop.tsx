"use client";

import { useState } from "react";

import { requestSummary } from "@/lib/api";
import type { QuestionResult, QuizItem, SummaryResponse } from "@/lib/types";

import { QuizQuestion } from "./QuizQuestion";

interface QuizLoopProps {
  quizzes: QuizItem[];
  onComplete: (summary: SummaryResponse) => void;
}

export function QuizLoop({ quizzes, onComplete }: QuizLoopProps) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [results, setResults] = useState<QuestionResult[]>([]);
  const [isFinishing, setIsFinishing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleResult(result: {
    question: string;
    topic: string;
    firstAttemptCorrect: boolean;
  }) {
    setResults((prev) => [
      ...prev,
      {
        question: result.question,
        topic: result.topic,
        first_attempt_correct: result.firstAttemptCorrect,
      },
    ]);
  }

  // By the time onNext fires (a separate click after the answer feedback is
  // shown), the results state from handleResult has already settled through
  // a render cycle, so it's safe to read directly here.
  async function handleNext() {
    if (currentIndex + 1 < quizzes.length) {
      setCurrentIndex((i) => i + 1);
      return;
    }

    setIsFinishing(true);
    setError(null);
    try {
      const summary = await requestSummary(results);
      onComplete(summary);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to compute your summary.");
    } finally {
      setIsFinishing(false);
    }
  }

  if (isFinishing) {
    return (
      <div className="flex flex-col items-center gap-4 py-24 text-center">
        <span className="h-3 w-3 animate-pulse rounded-full bg-(--color-accent)" />
        <p className="text-[15px] text-(--color-ink-muted)">Scoring your results…</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      <div className="h-1 w-full overflow-hidden rounded-full bg-(--color-border-soft)">
        <div
          className="h-full rounded-full bg-(--color-accent) transition-all duration-300 ease-out"
          style={{ width: `${((currentIndex + 1) / quizzes.length) * 100}%` }}
        />
      </div>
      <QuizQuestion
        key={currentIndex}
        quiz={quizzes[currentIndex]}
        index={currentIndex}
        total={quizzes.length}
        onResult={handleResult}
        onNext={handleNext}
      />
      {error && <p className="text-sm text-(--color-danger)">{error}</p>}
    </div>
  );
}
