<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import TarotCard from './TarotCard.vue'
import type { TarotCardData } from '@/types/tarot'

const props = defineProps<{ cards: TarotCardData[]; backUrl: string; locked?: boolean }>()
const emit = defineEmits<{ select: [card: TarotCardData]; interaction: [] }>()

const offset = ref(0)
const targetOffset = ref(0)
const dragX = ref<number | null>(null)
let animationFrame = 0

const positions = computed(() => {
  const total = props.cards.length
  return props.cards.map((card, index) => {
    const step = 360 / total
    const angle = index * step + offset.value
    const radians = (angle * Math.PI) / 180
    const x = Math.sin(radians) * 48
    const y = 42 - Math.cos(radians) * 44
    const visibility = Math.max(0, Math.cos(radians))
    return { card, angle, x, y, visibility, z: Math.round(visibility * 100) }
  })
})

const centeredCard = computed(() =>
  [...positions.value].sort((a, b) => b.visibility - a.visibility)[0]?.card,
)

function animate(): void {
  offset.value += (targetOffset.value - offset.value) * 0.11
  animationFrame = requestAnimationFrame(animate)
}

function rotateBy(delta: number): void {
  if (props.locked) return
  targetOffset.value += delta
  emit('interaction')
}

function shuffle(): void { rotateBy(1440 + Math.random() * 720) }
function stop(): void { targetOffset.value = offset.value }
function selectCentered(): void { if (!props.locked && centeredCard.value) emit('select', centeredCard.value) }

function onPointerDown(event: PointerEvent): void {
  if (props.locked) return
  dragX.value = event.clientX
  ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
}
function onPointerMove(event: PointerEvent): void {
  if (dragX.value === null || props.locked) return
  const delta = event.clientX - dragX.value
  dragX.value = event.clientX
  rotateBy(delta * 0.42)
}
function onPointerUp(): void { dragX.value = null }
function onWheel(event: WheelEvent): void { rotateBy(event.deltaY * 0.08 + event.deltaX * 0.08) }

watch(() => props.locked, (locked) => { if (locked) stop() })
onMounted(animate)
onBeforeUnmount(() => cancelAnimationFrame(animationFrame))

defineExpose({ rotateBy, shuffle, stop, selectCentered })
</script>

<template>
  <div
    class="wheel-stage"
    role="application"
    aria-label="Tarot card wheel. Drag or move your hand to rotate."
    @pointerdown="onPointerDown"
    @pointermove="onPointerMove"
    @pointerup="onPointerUp"
    @pointercancel="onPointerUp"
    @wheel.prevent="onWheel"
  >
    <div class="wheel-stage__halo"></div>
    <button
      v-for="item in positions"
      :key="item.card.id"
      class="wheel-card"
      :style="{
        '--x': `${item.x}vw`,
        '--y': `${item.y}vh`,
        '--rotation': `${item.angle}deg`,
        '--visibility': item.visibility,
        '--z': item.z,
      }"
      :aria-label="`Select ${item.card.name}`"
      :disabled="locked"
      @click.stop="emit('select', item.card)"
    >
      <TarotCard :back-url="backUrl" compact />
    </button>
    <button class="wheel-stage__focus" :disabled="locked" @click.stop="selectCentered">
      <span>DRAW</span>
      <small>pinch or tap</small>
    </button>
  </div>
</template>

<style scoped>
.wheel-stage { position: absolute; inset: 0; overflow: hidden; touch-action: none; cursor: grab; }
.wheel-stage:active { cursor: grabbing; }
.wheel-stage__halo { position: absolute; left: 50%; bottom: -24vh; width: 90vw; height: 52vh; transform: translateX(-50%); border-radius: 50%; background: radial-gradient(ellipse, rgba(139, 175, 242, .2), transparent 65%); filter: blur(28px); }
.wheel-card { position: absolute; left: 50%; top: 50%; z-index: var(--z); border: 0; padding: 0; background: transparent; opacity: calc(.1 + var(--visibility) * .9); transform: translate(calc(-50% + var(--x)), calc(-50% + var(--y))) rotate(var(--rotation)) scale(calc(.66 + var(--visibility) * .28)); filter: blur(calc((1 - var(--visibility)) * 2.6px)); transition: opacity .22s ease, filter .22s ease; }
.wheel-card:disabled { pointer-events: none; }
.wheel-stage__focus { position: absolute; left: 50%; bottom: 7.5vh; z-index: 130; transform: translateX(-50%); width: 88px; height: 88px; border-radius: 50%; border: 1px solid rgba(255,255,255,.45); color: #f8f5e9; background: rgba(245, 243, 233, .1); backdrop-filter: blur(18px); display: grid; place-content: center; gap: 2px; letter-spacing: .18em; cursor: pointer; }
.wheel-stage__focus span { font-size: 11px; }
.wheel-stage__focus small { font-size: 8px; letter-spacing: .08em; opacity: .62; }
@media (max-width: 760px) { .wheel-card { transform: translate(calc(-50% + var(--x)), calc(-50% + var(--y))) rotate(var(--rotation)) scale(calc(.52 + var(--visibility) * .24)); } }
</style>
