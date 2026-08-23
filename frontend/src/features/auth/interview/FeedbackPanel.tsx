import Card from '../../../components/ui/Card'
import { cn } from '../../../lib/cn'
import type { Feedback, ScoreDimension } from '../../../types'

const dimensionLabels: Record<ScoreDimension, string> = {
  correctness: 'Correctness',
  communication: 'Communication',
  depth: 'Depth',
  edge_cases: 'Edge cases',
}

function scoreColor(value: number) {
  if (value >= 8) return 'text-emerald-400'
  if (value >= 5) return 'text-amber-400'
  return 'text-red-400'
}

export default function FeedbackPanel({ feedback }: { feedback: Feedback }) {
  return (
    <Card className="space-y-6">
      <div className="grid gap-3 sm:grid-cols-2">
        {feedback.scores.map((score) => (
          <div key={score.dimension} className="rounded-lg border border-slate-800 p-3">
            <div className="flex items-baseline justify-between">
              <span className="text-sm text-slate-400">{dimensionLabels[score.dimension]}</span>
              <span className={cn('text-xl font-bold', scoreColor(score.value))}>
                {score.value}
                <span className="text-sm text-slate-600">/10</span>
              </span>
            </div>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-800">
              <div
                className="h-full rounded-full bg-indigo-500 transition-all duration-700"
                style={{ width: `${score.value * 10}%` }}
              />
            </div>
            <p className="mt-2 text-xs text-slate-500">{score.justification}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <h3 className="text-sm font-semibold text-emerald-400">Strengths</h3>
          <ul className="mt-2 space-y-1 text-sm text-slate-300">
            {feedback.strengths.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3 className="text-sm font-semibold text-amber-400">Improvements</h3>
          <ul className="mt-2 space-y-1 text-sm text-slate-300">
            {feedback.improvements.map((item) => (
              <li key={item}>• {item}</li>
            ))}
          </ul>
        </div>
      </div>

      {feedback.followUpQuestion && (
        <div className="rounded-lg border border-indigo-900 bg-indigo-950/40 p-4">
          <h3 className="text-sm font-semibold text-indigo-300">Follow-up question</h3>
          <p className="mt-1 text-sm text-slate-300">{feedback.followUpQuestion}</p>
        </div>
      )}
    </Card>
  )
}
