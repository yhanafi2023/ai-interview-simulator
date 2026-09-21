import { delay, http, HttpResponse } from 'msw'
import { API_BASE } from '../lib/config'
import { mockQuestions, mockUser } from './data'
import type {
  ApiError,
  AuthResponse,
  CreateSessionRequest,
  Feedback,
  LoginRequest,
  RegisterRequest,
  Session,
  SubmitAnswerRequest,
} from '../types'
const sessions = new Map<string, Session>()

let answerCounter = 0
export const handlers = [
  http.get(`${API_BASE}/questions`, async ({ request }) => {
    await delay(300)

    const url = new URL(request.url)
    const type = url.searchParams.get('type')
    const items = type ? mockQuestions.filter((q) => q.type === type) : mockQuestions

    return HttpResponse.json({ items, total: items.length })
  }),

  http.post<never, LoginRequest, AuthResponse | ApiError>(
    `${API_BASE}/auth/login`,
    async ({ request }) => {
      await delay(500)

      const body = await request.json()

      if (body.password !== 'password123') {
        return HttpResponse.json({ detail: 'Invalid email or password' }, { status: 401 })
      }

      return HttpResponse.json({
        accessToken: 'mock-access-token',
        user: { ...mockUser, email: body.email },
      })
    },
  ),

  http.get(`${API_BASE}/auth/me`, () => HttpResponse.json(mockUser)),
  http.post<never, RegisterRequest, AuthResponse | ApiError>(
    `${API_BASE}/auth/register`,
    async ({ request }) => {
      await delay(500)

      const body = await request.json()

      if (body.email === 'taken@example.com') {
        return HttpResponse.json({ detail: 'Email already registered' }, { status: 409 })
      }

      return HttpResponse.json(
        {
          accessToken: 'mock-access-token',
          user: {
            id: `usr_${Date.now()}`,
            email: body.email,
            displayName: body.displayName,
            role: 'user',
            createdAt: new Date().toISOString(),
          },
        },
        { status: 201 },
      )
    },
  ),
  http.post<never, CreateSessionRequest, Session>(`${API_BASE}/sessions`, async ({ request }) => {
    await delay(400)

    const body = await request.json()

    const pool = mockQuestions.filter((q) => q.type === body.type)
    const questions = (pool.length ? pool : mockQuestions).slice(0, body.questionCount)

    const session: Session = {
      id: `ses_${Date.now()}`,
      type: body.type,
      difficulty: body.difficulty,
      status: 'in_progress',
      createdAt: new Date().toISOString(),
      questions,
    }

    sessions.set(session.id, session)

    return HttpResponse.json(session, { status: 201 })
  }),

  http.get<{ sessionId: string }, never, Session | ApiError>(
    `${API_BASE}/sessions/:sessionId`,
    async ({ params }) => {
      await delay(200)

      const session = sessions.get(params.sessionId)

      if (!session) {
        return HttpResponse.json({ detail: 'Session not found' }, { status: 404 })
      }

      return HttpResponse.json(session)
    },
  ),

  http.post<{ sessionId: string }, SubmitAnswerRequest, Feedback>(
    `${API_BASE}/sessions/:sessionId/answers`,
    async ({ request }) => {
      await delay(1500)

      const body = await request.json()
      answerCounter += 1

      const length = body.content.trim().length
      const base = length > 400 ? 8 : length > 150 ? 6 : 4

      const feedback: Feedback = {
        answerId: `ans_${answerCounter}`,
        questionId: body.questionId,
        scores: [
          {
            dimension: 'correctness',
            value: base,
            justification: 'The core approach is sound but skips a key constraint.',
          },
          {
            dimension: 'communication',
            value: Math.min(10, base + 1),
            justification: 'Clear structure. State your assumptions earlier.',
          },
          {
            dimension: 'depth',
            value: Math.max(1, base - 1),
            justification: 'Time complexity is mentioned but not derived.',
          },
          {
            dimension: 'edge_cases',
            value: Math.max(1, base - 2),
            justification: 'Empty and single-element inputs are not addressed.',
          },
        ],
        strengths: [
          'You explained your approach before writing code.',
          'Variable naming was clear and consistent.',
        ],
        improvements: [
          'Walk through at least one edge case out loud.',
          'Give the time and space complexity explicitly.',
        ],
        followUpQuestion:
          length > 150
            ? 'How would your solution change if the input did not fit in memory?'
            : undefined,
      }

      return HttpResponse.json(feedback, { status: 201 })
    },
  ),
    http.post(`${API_BASE}/auth/refresh`, () =>
    HttpResponse.json({ detail: 'Invalid or expired session' }, { status: 401 }),
  ),

  http.post(`${API_BASE}/auth/logout`, () => new HttpResponse(null, { status: 204 })),
]
