import { useEffect, useState } from 'react'
import Badge from '../components/ui/Badge'
import Card from '../components/ui/Card'
import { API_BASE } from '../lib/config'
import type { Question } from '../types'

export default function Dashboard() {
  const [questions, setQuestions] = useState<Question[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch(`${API_BASE}/questions`)
      .then((res) => res.json())
      .then((data) => setQuestions(data.items))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Dashboard</h1>

      {loading ? (
        <p className="text-slate-400">Loading questions…</p>
      ) : (
        <div className="grid gap-4">
          {questions.map((q) => (
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
