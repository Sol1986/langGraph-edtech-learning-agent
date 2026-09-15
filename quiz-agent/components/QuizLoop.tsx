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
    return <p>Scoring your results...</p>;
  }

  return (
    <div className="flex flex-col gap-4">
      <QuizQuestion
        key={currentIndex}
        quiz={quizzes[currentIndex]}
        index={currentIndex}
        total={quizzes.length}
        onResult={handleResult}
        onNext={handleNext}
      />
      {error && <p className="text-red-600 dark:text-red-400 text-sm">{error}</p>}
    </div>
  );
}
