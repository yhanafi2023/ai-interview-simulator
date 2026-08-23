import { useMutation, useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate } from 'react-router'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import Select from '../components/ui/Select'
import { api } from '../lib/api'
import type {
  CreateSessionRequest,
  Difficulty,
  InterviewType,
  QuestionListResponse,
  Session,
} from '../types'

export default function Dashboard() {
  const navigate = useNavigate()

  const [type, setType] = useState<InterviewType>('technical')
  const [difficulty, setDifficulty] = useState<Difficulty>('medium')
  const [questionCount, setQuestionCount] = useState(3)

  const questions = useQuery({
    queryKey: ['questions'],
    queryFn: () => api.get<QuestionListResponse>('/questions'),
  })

  const createSession = useMutation({
    mutationFn: (body: CreateSessionRequest) => api.post<Session>('/sessions', body),
    onSuccess: (session) => navigate(`/interview/${session.id}`),
  })

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">Dashboard</h1>

      <Card className="space-y-4">
        <h2 className="text-lg font-semibold">Start an interview</h2>

        <div className="grid gap-4 sm:grid-cols-3">
          <Select
            label="Type"
            value={type}
            onChange={(e) => setType(e.target.value as InterviewType)}
          >
            <option value="technical">Technical</option>
            <option value="behavioral">Behavioral</option>
            <option value="system_design">System design</option>
          </Select>

          <Select
            label="Difficulty"
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value as Difficulty)}
          >
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </Select>

          <Select
            label="Questions"
            value={questionCount}
            onChange={(e) => setQuestionCount(Number(e.target.value))}
          >
            <option value={1}>1</option>
            <option value={3}>3</option>
            <option value={5}>5</option>
          </Select>
        </div>

        {createSession.isError && (
          <p className="text-sm text-red-400">{createSession.error.message}</p>
        )}

        <Button
          disabled={createSession.isPending}
          onClick={() => createSession.mutate({ type, difficulty, questionCount })}
        >
          {createSession.isPending ? 'Starting…' : 'Start interview'}
        </Button>
      </Card>

      <section className="space-y-3">
        <h2 className="text-lg font-semibold">Question bank</h2>

        {questions.isPending && <p className="text-slate-400">Loading questions…</p>}
        {questions.isError && <p className="text-red-400">{questions.error.message}</p>}

        {questions.data && (
          <div className="grid gap-4">
            {questions.data.items.map((q) => (
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
      </section>
    </div>
  )
}
