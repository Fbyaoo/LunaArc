import { defineStore } from 'pinia'

export const useTarotStore = defineStore('tarot', {
  state: () => ({
    cards: [] as any[]   // 明确为 any[] 类型
  }),
  actions: {
    setCards(cards: any[]) {
      this.cards = cards
    }
  }
})