import { delay, http, HttpResponse } from 'msw'
import { API_BASE } from '../lib/config'
import { mockQuestions, mockUser } from './data'
import type { ApiError, AuthResponse, LoginRequest, RegisterRequest } from '../types'

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
          },
        },
        { status: 201 },
      )
    },
  ),
]
