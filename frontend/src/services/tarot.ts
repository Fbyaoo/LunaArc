export type ReadingMode = 'daily' | 'quick' | 'deep'
export type SpreadType = 'daily_card' | 'single_card' | 'three_card'

export type ReadingStage =
  | 'intro'
  | 'question'
  | 'permission'
  | 'selecting'
  | 'drawing'
  | 'submitting'
  | 'awaiting_clarify'
  | 'success'
  | 'error'

export interface TarotCardData {
  id: number
  name: string
  imageUrl: string
  reversed: boolean
  position?: string
  interpretation?: string
  keywords?: string[]
}

export interface ReadingRequest {
  question: string | null
  spread_type: SpreadType
  cards: Array<{
    id: number
    reversed: boolean
    position?: string
  }>
}

export interface ReadingResponse {
  reading_id: string
  status: 'success' | 'awaiting_clarify'
  title: string
  summary: string
  cards: TarotCardData[]
  advice: string
  clarify_prompt?: string
  clarify_session_id?: string
}
