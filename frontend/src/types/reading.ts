import type { TarotCard } from './tarot'

/**
 * 原有 Agent 解读结果类型。
 * 保留它，避免破坏现有抽牌页面或 Agent 结果组件。
 */
export interface ReadingResult {
  summary: string
  cards: TarotCard[]
  connections: string
  advice: string[]
  reflectionQuestion: string
  disclaimer: string
}

/**
 * 后端使用的牌阵类型。
 */
export type SpreadType =
  | 'daily_card'
  | 'single_card'
  | 'three_card'

/**
 * 一次 Reading 在后端的处理状态。
 */
export type ReadingStatus =
  | 'pending'
  | 'awaiting_clarify'
  | 'completed'
  | 'failed'

/**
 * 历史记录详情中的单张牌。
 *
 * 这里不直接复用 TarotCard，
 * 因为历史接口还会返回 position、interpretation 等结果字段。
 */
export interface ReadingCard {
  card_id: number
  name: string
  image_url?: string | null
  position?: string | null
  reversed: boolean
  interpretation?: string | null
  keywords?: string[]
}

/**
 * Home 最近记录、History 列表、Saved 列表共同使用的摘要类型。
 */
export interface ReadingSummaryItem {
  id: string
  spread_type: SpreadType
  question: string | null
  title: string
  summary: string
  created_at: string
  saved: boolean
  status: ReadingStatus
}

/**
 * 单条历史记录完整详情。
 */
export interface ReadingDetail extends ReadingSummaryItem {
  cards: ReadingCard[]
  synthesis?: string | null
  advice?: string | null

  clarification?: {
    prompt: string
    answer: string
  } | null
}

/**
 * 历史记录分页响应。
 */
export interface PaginatedReadings {
  items: ReadingSummaryItem[]
  total: number
  page?: number
  page_size?: number
}

/**
 * 用户当天额度。
 */
export interface UsageSummary {
  plan: 'free' | 'plus' | string
  daily_limit: number | null
  used_today: number
  remaining_today: number | null
  reset_at: string | null
}

/**
 * AI Tarot Guide 会话。
 */
export interface GuideSession {
  session_id: string
  reading_id: string | null
  created_at: string
}

/**
 * Guide 单条消息。
 */
export interface GuideMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

/**
 * Guide 消息列表响应。
 */
export interface GuideMessageList {
  items: GuideMessage[]
}