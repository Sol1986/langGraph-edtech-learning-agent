// TypeScript mirrors of memorang/schemas.py

export interface UploadPdfResponse {
  thread_id: string;
  topic: string | null;
  learning_plan: string | null;
  status: string;
}

export interface QuizItem {
  question: string;
  correct_answer: string;
  wrong_answers: string[];
  explanation: string;
  topic: string;
  source_pages: number[];
}

export interface ResumeResponse {
  thread_id: string;
  status: string;
  quizzes: QuizItem[];
}

export interface HintResponse {
  hint: string;
  source_pages: number[];
}

export interface QuestionResult {
  question: string;
  topic: string;
  first_attempt_correct: boolean;
}

export interface SummaryResponse {
  total: number;
  correct_first_attempt: number;
  score_pct: number;
  passed: boolean;
  wrong_questions: QuestionResult[];
  topics_to_focus: string[];
  topics_understood: string[];
}
