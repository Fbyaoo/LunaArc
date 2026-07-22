import type { RouteRecordRaw } from 'vue-router'

export const yourSpaceRoutes: RouteRecordRaw[] = [
  { path: '/guide', name: 'ai-guide', component: () => import('@/pages/Guide/AITarotGuide.vue'), meta: { requiresAuth: true } },
  { path: '/history', name: 'reading-history', component: () => import('@/pages/History/ReadingHistory.vue'), meta: { requiresAuth: true } },
  { path: '/history/:readingId', name: 'reading-detail', component: () => import('@/pages/History/ReadingDetail.vue'), props: true, meta: { requiresAuth: true } },
  { path: '/saved-readings', name: 'saved-readings', component: () => import('@/pages/History/SavedReadings.vue'), meta: { requiresAuth: true } },
]
