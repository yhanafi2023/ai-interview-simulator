import { API_BASE } from './config'
import type { ApiError } from '../types'

export class ApiRequestError extends Error {
  public status: number
  public detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.status = status
    this.detail = detail
    this.name = 'ApiRequestError'
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  })

  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = (await res.json()) as ApiError
      detail = body.detail
    } catch {
      //
    }
    throw new ApiRequestError(res.status, detail)
  }

  if (res.status === 204) {
    return undefined as T
  }

  return (await res.json()) as T
}
export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'POST', body: JSON.stringify(body) }),
}
