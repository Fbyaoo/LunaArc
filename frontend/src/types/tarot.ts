import { defineStore } from 'pinia'

// 1️⃣ 导出 TarotCard 接口（定义卡片数据结构）
export interface TarotCard {
  id: number
  name: string
  suit?: string       // 可选属性，根据实际调整
  value?: number
  image?: string
  // ... 添加其他字段
}

// 2️⃣ Pinia Store 使用该类型
export const useTarotStore = defineStore('tarot', {
  state: () => ({
    cards: [] as TarotCard[]   // 明确类型为 TarotCard[]
  }),
  actions: {
    setCards(cards: TarotCard[]) {
      this.cards = cards
    }
  }
})