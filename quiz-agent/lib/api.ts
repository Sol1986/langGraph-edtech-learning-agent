import type {
  HintResponse,
  QuestionResult,
  ResumeResponse,
  SummaryResponse,
  UploadPdfResponse,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = body.detail ?? body.error ?? detail;
    } catch {
      // response body wasn't JSON; fall back to statusText
    }
    throw new Error(`${response.status}: ${detail}`);
  }
  return response.json() as Promise<T>;
}

export async function uploadPdf(file: File): Promise<UploadPdfResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE_URL}/api/upload-pdf`, {
    method: "POST",
    body: formData,
  });
  return handleResponse<UploadPdfResponse>(response);
}

export async function resumeThread(
  threadId: string,
  feedback: string | null,
): Promise<ResumeResponse> {
  const response = await fetch(`${API_BASE_URL}/api/resume/${threadId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ human_analyst_feedback: feedback || null }),
  });
  return handleResponse<ResumeResponse>(response);
}

export async function requestHint(
  question: string,
  correctAnswer: string,
  userMessage: string,
): Promise<HintResponse> {
  const response = await fetch(`${API_BASE_URL}/api/hint`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question,
      correct_answer: correctAnswer,
      user_message: userMessage,
    }),
  });
  return handleResponse<HintResponse>(response);
}

export async function requestSummary(results: QuestionResult[]): Promise<SummaryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/summary`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ results }),
  });
  return handleResponse<SummaryResponse>(response);
}
