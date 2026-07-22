import { apiFetch } from './http'
import type { GuideMessage, GuideSession } from '@/types/reading'

export function createGuideSession(readingId: string | null): Promise<GuideSession> {
  return apiFetch('/api/guide/sessions', {
    method: 'POST',
    body: JSON.stringify({ reading_id: readingId }),
  })
}

export function getGuideMessages(sessionId: string): Promise<{ items: GuideMessage[] }> {
  return apiFetch(`/api/guide/sessions/${encodeURIComponent(sessionId)}/messages`)
}

export function sendGuideMessage(sessionId: string, content: string): Promise<GuideMessage> {
  return apiFetch(`/api/guide/sessions/${encodeURIComponent(sessionId)}/messages`, {
    method: 'POST',
    body: JSON.stringify({ content }),
  })
}
