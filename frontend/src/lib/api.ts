import type { ApiError, AuthResponse } from '../types'
import { getAccessToken, setAccessToken } from './auth-store'
import { API_BASE } from './config'

export class ApiRequestError extends Error {
  public status: number
  public detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.name = 'ApiRequestError'
    this.status = status
    this.detail = detail
  }
}

let refreshPromise: Promise<boolean> | null = null

async function runRefresh(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
    })

    if (!res.ok) {
      setAccessToken(null)
      return false
    }

    const data = (await res.json()) as AuthResponse
    setAccessToken(data.accessToken)
    return true
  } catch {
    setAccessToken(null)
    return false
  }
}

function attemptRefresh(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = runRefresh().finally(() => {
      refreshPromise = null
    })
  }
  return refreshPromise
}

async function request<T>(path: string, options: RequestInit = {}, allowRetry = true): Promise<T> {
  const token = getAccessToken()

  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })

  if (res.status === 401 && allowRetry && !path.startsWith('/auth/')) {
    const refreshed = await attemptRefresh()
    if (refreshed) {
      return request<T>(path, options, false)
    }
  }

  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = (await res.json()) as ApiError
      detail = body.detail ?? detail
    } catch {
      // body wasn't JSON
    }
    throw new ApiRequestError(res.status, detail)
  }

  if (res.status === 204) return undefined as T

  return (await res.json()) as T
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown, headers?: Record<string, string>) =>
    request<T>(path, {
      method: 'POST',
      ...(headers ? { headers } : {}),
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    }),
}