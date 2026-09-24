import { getAccessToken } from './auth-store'
import { API_BASE } from './config'

export type JobEvent = { status: string }

export function streamJob(
  jobId: string,
  onEvent: (event: JobEvent) => void,
): () => void {
  const controller = new AbortController()

  void (async () => {
    try {
      const response = await fetch(`${API_BASE}/jobs/${jobId}/stream`, {
        headers: { Authorization: `Bearer ${getAccessToken() ?? ''}` },
        credentials: 'include',
        signal: controller.signal,
      })

      if (!response.ok || !response.body) return

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const chunks = buffer.split('\n\n')
        buffer = chunks.pop() ?? ''

        for (const chunk of chunks) {
          const line = chunk.split('\n').find((l) => l.startsWith('data:'))
          if (!line) continue
          try {
            onEvent(JSON.parse(line.slice(5).trim()) as JobEvent)
          } catch {
            // ignore malformed frames
          }
        }
      }
    } catch {
      // aborted or network failure — the polling fallback covers it
    }
  })()

  return () => controller.abort()
}