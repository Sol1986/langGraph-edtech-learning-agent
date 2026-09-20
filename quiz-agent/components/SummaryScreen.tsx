import type { SummaryResponse } from "@/lib/types";

interface SummaryScreenProps {
  summary: SummaryResponse;
}

// Purely a display component: renders the /api/summary response as-is.
// No computation and no LLM call happens here -- the summary is deterministic,
// computed server-side in summary.py from data the graph already generated.
export function SummaryScreen({ summary }: SummaryScreenProps) {
  const scorePct = Math.round(summary.score_pct * 100);

  return (
    <div className="flex flex-col items-center gap-10 text-center">
      <div className="flex flex-col items-center gap-3">
        <span
          className={`text-sm font-medium ${
            summary.passed ? "text-(--color-success)" : "text-(--color-danger)"
          }`}
        >
          {summary.passed ? "You passed" : "Not quite there yet"}
        </span>
        <div className="flex items-baseline gap-2">
          <span className="text-7xl font-semibold tracking-tight">{scorePct}</span>
          <span className="text-3xl font-semibold text-(--color-ink-muted)">%</span>
        </div>
        <p className="text-[15px] text-(--color-ink-muted)">
          {summary.correct_first_attempt} of {summary.total} correct on the first attempt
        </p>
      </div>

      <div className="grid w-full gap-4 text-left sm:grid-cols-2">
        {summary.topics_understood.length > 0 && (
          <div className="rounded-2xl border border-(--color-success-border) bg-(--color-success-bg) p-5">
            <h3 className="text-sm font-semibold text-(--color-success)">Topics you understand well</h3>
            <ul className="mt-2 flex flex-col gap-1 text-[14px] text-(--color-ink)">
              {summary.topics_understood.map((topic) => (
                <li key={topic}>{topic}</li>
              ))}
            </ul>
          </div>
        )}

        {summary.topics_to_focus.length > 0 && (
          <div className="rounded-2xl border border-(--color-danger-border) bg-(--color-danger-bg) p-5">
            <h3 className="text-sm font-semibold text-(--color-danger)">Topics to focus on</h3>
            <ul className="mt-2 flex flex-col gap-1 text-[14px] text-(--color-ink)">
              {summary.topics_to_focus.map((topic) => (
                <li key={topic}>{topic}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {summary.wrong_questions.length > 0 && (
        <div className="w-full rounded-2xl border border-(--color-border-soft) bg-(--color-surface) p-5 text-left">
          <h3 className="text-sm font-semibold">Questions you got wrong</h3>
          <ul className="mt-2 flex flex-col gap-1.5 text-[14px] text-(--color-ink-muted)">
            {summary.wrong_questions.map((q, i) => (
              <li key={i}>
                {q.question} <span className="text-(--color-ink-muted)/70">({q.topic})</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
