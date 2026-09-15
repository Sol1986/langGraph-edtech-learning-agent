"use client";

import { useMemo, useState } from "react";

import type { QuizItem } from "@/lib/types";

import { HintChat } from "./HintChat";

interface QuizQuestionProps {
  quiz: QuizItem;
  index: number;
  total: number;
  onResult: (result: { question: string; topic: string; firstAttemptCorrect: boolean }) => void;
  onNext: () => void;
}

function shuffle<T>(items: T[]): T[] {
  const copy = [...items];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

export function QuizQuestion({ quiz, index, total, onResult, onNext }: QuizQuestionProps) {
  const options = useMemo(
    () => shuffle([quiz.correct_answer, ...quiz.wrong_answers]),
    [quiz],
  );
  const [selected, setSelected] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);
  const [attempts, setAttempts] = useState(0);

  const isCorrect = submitted && selected === quiz.correct_answer;
  const isIncorrect = submitted && selected !== quiz.correct_answer;

  function handleSubmit() {
    if (!selected) return;
    const correct = selected === quiz.correct_answer;

    // Score only the first attempt -- retries let the learner reach the
    // correct answer without further hurting the score (no penalty).
    if (attempts === 0) {
      onResult({ question: quiz.question, topic: quiz.topic, firstAttemptCorrect: correct });
    }
    setAttempts((a) => a + 1);
    setSubmitted(true);
  }

  function handleRetry() {
    setSelected(null);
    setSubmitted(false);
  }

  return (
    <div className="flex flex-col gap-4 max-w-2xl">
      <p className="text-sm text-gray-500 dark:text-gray-400">
        Question {index + 1} of {total} &middot; {quiz.topic}
      </p>
      <h2 className="text-lg font-medium">{quiz.question}</h2>

      <div className="flex flex-col gap-2">
        {options.map((option) => (
          <label
            key={option}
            className={`border rounded px-3 py-2 cursor-pointer ${
              // Only highlight the correct option once the learner actually
              // picks it -- highlighting it on a wrong attempt would reveal
              // the answer instead of letting them retry.
              isCorrect && option === quiz.correct_answer
                ? "border-green-600 bg-green-50 text-green-900 dark:border-green-500 dark:bg-green-950 dark:text-green-100"
                : ""
            } ${
              isIncorrect && option === selected
                ? "border-red-600 bg-red-50 text-red-900 dark:border-red-500 dark:bg-red-950 dark:text-red-100"
                : ""
            }`}
          >
            <input
              type="radio"
              name={`quiz-${index}`}
              value={option}
              checked={selected === option}
              onChange={() => setSelected(option)}
              disabled={submitted}
              className="mr-2"
            />
            {option}
          </label>
        ))}
      </div>

      {!submitted && (
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!selected}
          className="rounded bg-blue-600 text-white px-4 py-2 self-start disabled:opacity-50"
        >
          Submit
        </button>
      )}

      {isCorrect && (
        <div className="border border-green-600 dark:border-green-500 bg-green-50 dark:bg-green-950 rounded p-3">
          <p className="font-medium text-green-800 dark:text-green-200">Correct!</p>
          <p className="text-sm text-green-900 dark:text-green-100">{quiz.explanation}</p>
          {quiz.source_pages.length > 0 && (
            <p className="text-xs text-green-700 dark:text-green-400">
              Referenced from page(s): {quiz.source_pages.join(", ")}
            </p>
          )}
          <button
            type="button"
            onClick={onNext}
            className="mt-3 rounded bg-green-700 text-white px-4 py-2"
          >
            Next
          </button>
        </div>
      )}

      {isIncorrect && (
        <div className="flex flex-col gap-3">
          <div className="border border-red-600 dark:border-red-500 bg-red-50 dark:bg-red-950 rounded p-3">
            <p className="font-medium text-red-800 dark:text-red-200">Not quite -- try again.</p>
            {quiz.source_pages.length > 0 && (
              <p className="text-xs text-red-700 dark:text-red-400">
                Hint: check page(s) {quiz.source_pages.join(", ")}
              </p>
            )}
            <button
              type="button"
              onClick={handleRetry}
              className="mt-3 rounded bg-red-700 text-white px-4 py-2"
            >
              Retry
            </button>
          </div>
          <HintChat question={quiz.question} correctAnswer={quiz.correct_answer} />
        </div>
      )}
    </div>
  );
}
