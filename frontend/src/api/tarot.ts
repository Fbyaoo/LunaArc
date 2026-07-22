import type { ReadingRequest, ReadingResponse } from '@/types/tarot'

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

async function requestJson<T>(path: string, init: RequestInit): Promise<T> {
  const token = localStorage.getItem('access_token')
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...init.headers,
    },
  })

  if (!response.ok) {
    const message = await response.text().catch(() => '')
    throw new Error(message || `Request failed with ${response.status}`)
  }

  return response.json() as Promise<T>
}

export function createTarotReading(payload: ReadingRequest): Promise<ReadingResponse> {
  return requestJson<ReadingResponse>('/api/readings/draw-and-read', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export function clarifyTarotReading(
  sessionId: string,
  clarification: string,
): Promise<ReadingResponse> {
  return requestJson<ReadingResponse>('/api/readings/clarify', {
    method: 'POST',
    headers: { 'X-Clarify-Session-Id': sessionId },
    body: JSON.stringify({ clarification }),
  })
}
