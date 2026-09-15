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
    <main className="flex flex-col gap-8 p-8 max-w-3xl mx-auto">
      <h1 className="text-5xl font-bold text-center">AI Learning Agent</h1>

      {stage === "upload" && <PdfUploadForm onUploaded={handleUploaded} />}

      {stage === "reviewing_plan" && uploadResult && (
        <LearningPlanApproval
          threadId={uploadResult.thread_id}
          topic={uploadResult.topic}
          learningPlan={uploadResult.learning_plan}
          onApproved={handleApproved}
        />
      )}

      {stage === "quiz" && quizzes.length > 0 && (
        <QuizLoop quizzes={quizzes} onComplete={handleQuizComplete} />
      )}

      {stage === "summary" && summary && (
        <div className="flex flex-col gap-4">
          <SummaryScreen summary={summary} />
          <button
            type="button"
            onClick={handleRestart}
            className="rounded bg-gray-700 text-white px-4 py-2 self-start"
          >
            Start a new lesson
          </button>
        </div>
      )}
    </main>
  );
}
