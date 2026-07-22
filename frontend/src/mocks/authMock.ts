import type { LunaUser } from '../types/home'

export const MOCK_SESSION_KEY = 'lunaarc.mock.session'

export interface MockSession {
  accessToken: string
  refreshToken: string
  expiresAt: number
  user: LunaUser
}

const mockUser: LunaUser = {
  id: 'usr_luna_001',
  displayName: 'Luna',
  email: 'luna@lunaarc.app',
  plan: 'free',
  planLabel: 'Free Plan',
  freeReadingsRemaining: 2,
  dailyReadingLimit: 3,
}

export function createMockSession(): MockSession {
  const session: MockSession = {
    accessToken: 'mock_access_token_luna',
    refreshToken: 'mock_refresh_token_luna',
    expiresAt: Date.now() + 1000 * 60 * 60 * 24,
    user: mockUser,
  }

  localStorage.setItem(MOCK_SESSION_KEY, JSON.stringify(session))

  return session
}

export function getMockSession(): MockSession | null {
  const storedSession = localStorage.getItem(MOCK_SESSION_KEY)

  if (!storedSession) {
    return null
  }

  try {
    const parsedSession = JSON.parse(storedSession) as MockSession

    if (!parsedSession.accessToken || !parsedSession.user) {
      clearMockSession()
      return null
    }

    if (parsedSession.expiresAt <= Date.now()) {
      clearMockSession()
      return null
    }

    return parsedSession
  } catch {
    clearMockSession()
    return null
  }
}

export function clearMockSession(): void {
  localStorage.removeItem(MOCK_SESSION_KEY)
}

export function updateMockUser(
  updates: Partial<LunaUser>,
): MockSession | null {
  const currentSession = getMockSession()

  if (!currentSession) {
    return null
  }

  const nextSession: MockSession = {
    ...currentSession,
    user: {
      ...currentSession.user,
      ...updates,
    },
  }

  localStorage.setItem(MOCK_SESSION_KEY, JSON.stringify(nextSession))

  return nextSession
}