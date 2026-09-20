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
    <div className="flex flex-col gap-6">
      <p className="text-sm font-medium text-(--color-accent)">
        Question {index + 1} of {total} &middot; {quiz.topic}
      </p>
      <h2 className="text-2xl font-semibold tracking-tight text-balance">{quiz.question}</h2>

      <div className="flex flex-col gap-2.5">
        {options.map((option) => {
          const isPickedCorrect = isCorrect && option === quiz.correct_answer;
          const isPickedWrong = isIncorrect && option === selected;

          return (
            <label
              key={option}
              className={`flex cursor-pointer items-center gap-3 rounded-2xl border px-4 py-3.5 text-[15px] transition ${
                isPickedCorrect
                  ? "border-(--color-success-border) bg-(--color-success-bg) text-(--color-success)"
                  : isPickedWrong
                    ? "border-(--color-danger-border) bg-(--color-danger-bg) text-(--color-danger)"
                    : selected === option
                      ? "border-(--color-accent) bg-(--color-accent)/5"
                      : "border-(--color-border-soft) bg-white hover:border-(--color-border)"
              } ${submitted ? "cursor-default" : ""}`}
            >
              <input
                type="radio"
                name={`quiz-${index}`}
                value={option}
                checked={selected === option}
                onChange={() => setSelected(option)}
                disabled={submitted}
                className="sr-only"
              />
              <span
                className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border ${
                  isPickedCorrect
                    ? "border-(--color-success) bg-(--color-success)"
                    : isPickedWrong
                      ? "border-(--color-danger) bg-(--color-danger)"
                      : selected === option
                        ? "border-(--color-accent) bg-(--color-accent)"
                        : "border-(--color-border)"
                }`}
              >
                {(selected === option || isPickedCorrect) && (
                  <span className="h-2 w-2 rounded-full bg-white" />
                )}
              </span>
              {option}
            </label>
          );
        })}
      </div>

      {!submitted && (
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!selected}
          className="self-start rounded-full bg-(--color-accent) px-6 py-3 text-[15px] font-medium text-white transition hover:bg-(--color-accent-hover) active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40"
        >
          Submit
        </button>
      )}

      {isCorrect && (
        <div className="rounded-2xl border border-(--color-success-border) bg-(--color-success-bg) p-5">
          <p className="font-medium text-(--color-success)">Correct!</p>
          <p className="mt-1 text-[15px] text-(--color-ink-muted)">{quiz.explanation}</p>
          {quiz.source_pages.length > 0 && (
            <p className="mt-2 text-xs text-(--color-ink-muted)">
              Referenced from page(s): {quiz.source_pages.join(", ")}
            </p>
          )}
          <button
            type="button"
            onClick={onNext}
            className="mt-4 rounded-full bg-(--color-success) px-6 py-2.5 text-[15px] font-medium text-white transition hover:opacity-90 active:scale-[0.98]"
          >
            Next
          </button>
        </div>
      )}

      {isIncorrect && (
        <div className="flex flex-col gap-4">
          <div className="rounded-2xl border border-(--color-danger-border) bg-(--color-danger-bg) p-5">
            <p className="font-medium text-(--color-danger)">Not quite — try again.</p>
            {quiz.source_pages.length > 0 && (
              <p className="mt-1 text-xs text-(--color-ink-muted)">
                Hint: check page(s) {quiz.source_pages.join(", ")}
              </p>
            )}
            <button
              type="button"
              onClick={handleRetry}
              className="mt-4 rounded-full bg-(--color-danger) px-6 py-2.5 text-[15px] font-medium text-white transition hover:opacity-90 active:scale-[0.98]"
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
