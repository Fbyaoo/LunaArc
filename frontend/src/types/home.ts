export type SubscriptionPlan = 'guest' | 'free' | 'plus'

export type ReadingModeId =
  | 'daily-fortune'
  | 'quick-question'
  | 'deep-reading'

export type NavigationId =
  | 'home'
  | 'daily-fortune'
  | 'quick-question'
  | 'deep-reading'
  | 'ai-guide'
  | 'history'
  | 'saved'
  | 'profile'
  | 'subscription'
  | 'settings'

export interface LunaUser {
  id: string
  displayName: string
  email: string
  avatarUrl?: string
  plan: SubscriptionPlan
  planLabel: string
  freeReadingsRemaining: number
  dailyReadingLimit: number
  renewalDate?: string
}

export interface SidebarNavigationItem {
  id: NavigationId
  label: string
  route: string
  icon:
    | 'home'
    | 'sparkle'
    | 'question'
    | 'cards'
    | 'guide'
    | 'history'
    | 'bookmark'
    | 'profile'
    | 'subscription'
    | 'settings'
}

export interface SidebarNavigationGroup {
  id: string
  label: string
  items: SidebarNavigationItem[]
}

export interface ReadingMode {
  id: ReadingModeId
  title: string
  eyebrow: string
  description: string
  route: string
  tone: 'blue' | 'mist' | 'white'
}

export interface RecentReading {
  id: string
  title: string
  modeLabel: string
  summary: string
  createdAt: string
  saved: boolean
}