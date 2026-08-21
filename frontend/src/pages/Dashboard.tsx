import { useQuery } from '@tanstack/react-query'
import Badge from '../components/ui/Badge'
import Card from '../components/ui/Card'
import { api } from '../lib/api'
import type { QuestionListResponse } from '../types'

export default function Dashboard() {
  const { data, isPending, isError, error } = useQuery({
    queryKey: ['questions'],
    queryFn: () => api.get<QuestionListResponse>('/questions'),
  })
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Dashboard</h1>

      {isPending && <p className="text-slate-400">Loading questions…</p>}
      {isError && <p className="text-red-400">Couldn't load questions: {error.message}</p>}
      {data && (
        <div className="grid gap-4">
          {data.items.map((q) => (
            <Card key={q.id}>
              <div className="mb-2 flex gap-2">
                <Badge tone="info">{q.type}</Badge>
                <Badge>{q.difficulty}</Badge>
              </div>
              <p>{q.prompt}</p>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
