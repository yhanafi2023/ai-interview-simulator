import { useMutation, useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router'
import Badge from '../components/ui/Badge'
import Button from '../components/ui/Button'
import Card from '../components/ui/Card'
import FeedbackPanel from '../features/auth/interview/FeedbackPanel'
import { api } from '../lib/api'
import type { GradingJob, Session, SubmitAnswerRequest } from '../types'
import { useEffect } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { streamJob } from '../lib/job-stream'

const STATUS_LABEL: Record<string, string> = {
  queued: 'Waiting for a grader…',
  running: 'Analyzing your answer…',
}

export default function InterviewRoom() {
  const { sessionId } = useParams<{ sessionId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [index, setIndex] = useState(0)
  const [answer, setAnswer] = useState('')
  const [jobId, setJobId] = useState<string | null>(null)

  const {
    data: session,
    isPending,
    isError,
    error,
  } = useQuery({
    queryKey: ['session', sessionId],
    queryFn: () => api.get<Session>(`/sessions/${sessionId}`),
    enabled: Boolean(sessionId),
  })

  const submit = useMutation({
    mutationFn: (body: SubmitAnswerRequest) =>
      api.post<GradingJob>(`/sessions/${sessionId}/answers`, body),
    onSuccess: (job) => setJobId(job.id),
  })

    const jobQuery = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => api.get<GradingJob>(`/jobs/${jobId}`),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'succeeded' || status === 'failed' ? false : 10000
    },
  })

  useEffect(() => {
    if (!jobId) return

    const stop = streamJob(jobId, (event) => {
      queryClient.setQueryData<GradingJob>(['job', jobId], (previous) =>
        previous ? { ...previous, status: event.status as GradingJob['status'] } : previous,
      )

      if (event.status === 'succeeded' || event.status === 'failed') {
        void queryClient.invalidateQueries({ queryKey: ['job', jobId] })
      }
    })

    return stop
  }, [jobId, queryClient])

  if (isPending) return <p className="text-slate-400">Loading session…</p>
  if (isError) return <p className="text-red-400">{error.message}</p>

  const question = session.questions[index]
  const isLastQuestion = index === session.questions.length - 1

  const job = jobQuery.data
  const feedback = job?.status === 'succeeded' ? job.feedback : undefined
  const isGrading = Boolean(jobId) && job?.status !== 'succeeded' && job?.status !== 'failed'

  function goToNextQuestion() {
    setIndex((current) => current + 1)
    setAnswer('')
    setJobId(null)
    submit.reset()
  }

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card className="h-fit">
        <div className="flex items-center justify-between">
          <span className="text-sm text-slate-400">
            Question {index + 1} of {session.questions.length}
          </span>
          <div className="flex gap-2">
            <Badge tone="info">{session.type}</Badge>
            <Badge>{question.difficulty}</Badge>
          </div>
        </div>
        <p className="mt-4 text-lg leading-relaxed">{question.prompt}</p>
      </Card>

      <div className="space-y-4">
        <Card>
          <label htmlFor="answer" className="block text-sm font-medium text-slate-300">
            Your answer
          </label>
          <textarea
            id="answer"
            value={answer}
            onChange={(event) => setAnswer(event.target.value)}
            disabled={Boolean(jobId)}
            rows={10}
            maxLength={6000}
            placeholder="Explain your approach first, then walk through the solution…"
            className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 p-3 text-sm text-slate-100 placeholder:text-slate-600 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-400 disabled:opacity-60"
          />

          <div className="mt-3 flex items-center justify-between">
            <span className="text-xs text-slate-500">{answer.trim().length} / 6000</span>
            {!jobId && (
              <Button
                disabled={answer.trim().length === 0 || submit.isPending}
                onClick={() => submit.mutate({ questionId: question.id, content: answer })}
              >
                {submit.isPending ? 'Submitting…' : 'Submit answer'}
              </Button>
            )}
          </div>
        </Card>

        {submit.isError && (
          <Card>
            <p className="text-sm text-red-400">Could not submit: {submit.error.message}</p>
          </Card>
        )}

        {isGrading && (
          <Card>
            <p className="animate-pulse text-sm text-slate-400">
              {STATUS_LABEL[job?.status ?? 'queued'] ?? 'Waiting…'}
            </p>
          </Card>
        )}

        {job?.status === 'failed' && (
          <Card>
            <p className="text-sm text-red-400">
              Grading failed{job.error ? `: ${job.error}` : ''}
            </p>
            <Button size="sm" variant="secondary" className="mt-3" onClick={goToNextQuestion}>
              Skip to next question
            </Button>
          </Card>
        )}

        {feedback && (
          <>
            <FeedbackPanel feedback={feedback} />
            {isLastQuestion ? (
              <Button variant="secondary" className="w-full" onClick={() => navigate('/dashboard')}>
                Finish session
              </Button>
            ) : (
              <Button className="w-full" onClick={goToNextQuestion}>
                Next question
              </Button>
            )}
          </>
        )}
      </div>
    </div>
  )
}