<script setup lang="ts">
import type { TarotCardData } from '@/types/tarot'

withDefaults(
  defineProps<{
    card?: TarotCardData
    backUrl: string
    revealed?: boolean
    selected?: boolean
    compact?: boolean
  }>(),
  { revealed: false, selected: false, compact: false },
)
</script>

<template>
  <article
    class="tarot-card"
    :class="{ 'is-revealed': revealed, 'is-selected': selected, 'is-compact': compact }"
  >
    <div class="tarot-card__inner" :class="{ 'is-reversed': revealed && card?.reversed }">
      <div class="tarot-card__face tarot-card__back">
        <img :src="backUrl" alt="Tarot card back" draggable="false" />
      </div>
      <div class="tarot-card__face tarot-card__front">
        <img v-if="card" :src="card.imageUrl" :alt="card.name" draggable="false" />
      </div>
    </div>
  </article>
</template>

<style scoped>
.tarot-card { width: clamp(116px, 10vw, 174px); aspect-ratio: 2 / 3.18; perspective: 1200px; }
.tarot-card.is-compact { width: clamp(82px, 7vw, 126px); }
.tarot-card__inner { width: 100%; height: 100%; position: relative; transform-style: preserve-3d; transition: transform 1.15s cubic-bezier(.18,.82,.26,1); }
.tarot-card.is-revealed .tarot-card__inner { transform: rotateY(180deg); }
.tarot-card__inner.is-reversed { transform: rotateY(180deg) rotateZ(180deg); }
.tarot-card__face { position: absolute; inset: 0; overflow: hidden; border-radius: 14px; backface-visibility: hidden; box-shadow: 0 24px 70px rgba(4, 14, 52, .34); }
.tarot-card__face::after { content: ''; position: absolute; inset: 0; border: 1px solid rgba(244, 240, 225, .52); border-radius: inherit; pointer-events: none; }
.tarot-card__front { transform: rotateY(180deg); background: #08133b; }
.tarot-card img { width: 100%; height: 100%; object-fit: cover; display: block; user-select: none; }
.tarot-card__back img { filter: saturate(.72) hue-rotate(168deg) brightness(.88); }
.tarot-card.is-selected { filter: drop-shadow(0 0 26px rgba(131, 174, 255, .48)); }
@media (prefers-reduced-motion: reduce) { .tarot-card__inner { transition-duration: .01ms; } }
</style>
