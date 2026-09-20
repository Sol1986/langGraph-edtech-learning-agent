"use client";

import { useState } from "react";

import { LearningPlanApproval } from "@/components/LearningPlanApproval";
import { PdfUploadForm } from "@/components/PdfUploadForm";
import { QuizLoop } from "@/components/QuizLoop";
import { SummaryScreen } from "@/components/SummaryScreen";
import type { QuizItem, SummaryResponse, UploadPdfResponse } from "@/lib/types";

type Stage = "upload" | "reviewing_plan" | "quiz" | "summary";

export default function Home() {
  const [stage, setStage] = useState<Stage>("upload");
  const [uploadResult, setUploadResult] = useState<UploadPdfResponse | null>(null);
  const [quizzes, setQuizzes] = useState<QuizItem[]>([]);
  const [summary, setSummary] = useState<SummaryResponse | null>(null);

  function handleUploaded(response: UploadPdfResponse) {
    setUploadResult(response);
    setStage("reviewing_plan");
  }

  function handleApproved(approvedQuizzes: QuizItem[]) {
    setQuizzes(approvedQuizzes);
    setStage("quiz");
  }

  function handleQuizComplete(finalSummary: SummaryResponse) {
    setSummary(finalSummary);
    setStage("summary");
  }

  function handleRestart() {
    setUploadResult(null);
    setQuizzes([]);
    setSummary(null);
    setStage("upload");
  }

  return (
    <div className="flex min-h-full flex-1 flex-col">
      <header className="sticky top-0 z-10 border-b border-(--color-border-soft) bg-white/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-5xl items-center px-6 py-4">
          <span className="text-[15px] font-semibold tracking-tight">AI Learning Agent</span>
        </div>
      </header>

      <main className="flex flex-1 flex-col">
        {stage === "upload" && (
          <section className="flex flex-1 flex-col items-center px-6 pt-20 pb-24 text-center">
            <h1 className="max-w-2xl text-5xl font-semibold tracking-tight text-balance sm:text-6xl">
              Learn anything, one PDF at a time.
            </h1>
            <p className="mt-5 max-w-xl text-lg text-(--color-ink-muted) text-balance sm:text-xl">
              Upload a document and get a tailored lesson plan, a ten-question quiz, and
              hints grounded in your own material.
            </p>
            <div className="mt-12 w-full max-w-lg">
              <PdfUploadForm onUploaded={handleUploaded} />
            </div>
          </section>
        )}

        {stage === "reviewing_plan" && uploadResult && (
          <section className="mx-auto w-full max-w-3xl px-6 py-16">
            <LearningPlanApproval
              threadId={uploadResult.thread_id}
              topic={uploadResult.course_topic}
              learningPlan={uploadResult.learning_plan}
              onApproved={handleApproved}
            />
          </section>
        )}

        {stage === "quiz" && quizzes.length > 0 && (
          <section className="mx-auto w-full max-w-2xl px-6 py-16">
            <QuizLoop quizzes={quizzes} onComplete={handleQuizComplete} />
          </section>
        )}

        {stage === "summary" && summary && (
          <section className="mx-auto flex w-full max-w-2xl flex-col gap-8 px-6 py-16">
            <SummaryScreen summary={summary} />
            <button
              type="button"
              onClick={handleRestart}
              className="self-center rounded-full bg-(--color-surface) px-6 py-3 text-[15px] font-medium text-(--color-ink) transition hover:bg-(--color-border-soft) active:scale-[0.98]"
            >
              Start a new lesson
            </button>
          </section>
        )}
      </main>
    </div>
  );
}
