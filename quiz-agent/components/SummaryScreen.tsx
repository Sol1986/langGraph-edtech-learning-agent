import type { SummaryResponse } from "@/lib/types";

interface SummaryScreenProps {
  summary: SummaryResponse;
}

// Purely a display component: renders the /api/summary response as-is.
// No computation and no LLM call happens here -- the summary is deterministic,
// computed server-side in summary.py from data the graph already generated.
export function SummaryScreen({ summary }: SummaryScreenProps) {
  return (
    <div className="flex flex-col gap-4 max-w-2xl">
      <h2 className={`text-2xl font-bold ${summary.passed ? "text-green-700" : "text-red-700"}`}>
        {summary.passed ? "Pass" : "Fail"}
      </h2>
      <p>
        Score: {summary.correct_first_attempt} / {summary.total} (
        {Math.round(summary.score_pct * 100)}%)
      </p>

      {summary.wrong_questions.length > 0 && (
        <div>
          <h3 className="font-semibold">Questions you got wrong</h3>
          <ul className="list-disc list-inside">
            {summary.wrong_questions.map((q, i) => (
              <li key={i}>
                {q.question} <span className="text-gray-500 dark:text-gray-400">({q.topic})</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {summary.topics_to_focus.length > 0 && (
        <div>
          <h3 className="font-semibold">Topics to focus on</h3>
          <ul className="list-disc list-inside">
            {summary.topics_to_focus.map((topic) => (
              <li key={topic}>{topic}</li>
            ))}
          </ul>
        </div>
      )}

      {summary.topics_understood.length > 0 && (
        <div>
          <h3 className="font-semibold">Topics you understand well</h3>
          <ul className="list-disc list-inside">
            {summary.topics_understood.map((topic) => (
              <li key={topic}>{topic}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
