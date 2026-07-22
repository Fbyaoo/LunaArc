<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref } from 'vue'
import CardWheel from './CardWheel.vue'
import TarotCard from './TarotCard.vue'
import { createTarotReading, clarifyTarotReading } from '@/api/tarot'
import { MediaPipeGestureController } from '@/services/mediapipeGesture'
import { YoloGestureClient } from '@/services/yoloGesture'
import type { GestureEvent } from '@/types/gesture'
import type { ReadingMode, ReadingResponse, ReadingStage, SpreadType, TarotCardData } from '@/types/tarot'

const props = defineProps<{ mode: ReadingMode }>()

const cardModules = import.meta.glob('@/assets/tarot/cards/*', { eager: true, import: 'default' }) as Record<string, string>
const backUrl = new URL('../../assets/tarot/card-back.jpg', import.meta.url).href
const names = [
  'The Fool','The Magician','The High Priestess','The Empress','The Emperor','The Hierophant',
  'The Lovers','The Chariot','Strength','The Hermit','Wheel of Fortune','Justice','The Hanged One',
  'Death','Temperance','The Devil','The Tower','The Star','The Moon','The Sun','Judgement','The World',
]
const deck = names.map<TarotCardData>((name, id) => ({
  id,
  name,
  imageUrl: Object.entries(cardModules).find(([path]) => path.endsWith(`/${id}.png`))?.[1] ?? '',
  reversed: false,
}))

const config = computed(() => ({
  daily: { label: 'DAILY FORTUNE', title: 'Meet the energy already moving toward you.', subtitle: 'One card. No question required.', spread: 'daily_card' as SpreadType, count: 1 },
  quick: { label: 'QUICK QUESTION', title: 'Place one clear thought into the room.', subtitle: 'One card will answer what feels closest.', spread: 'single_card' as SpreadType, count: 1 },
  deep: { label: 'DEEP READING', title: 'Stay long enough for the pattern to appear.', subtitle: 'Three cards. One connected reflection.', spread: 'three_card' as SpreadType, count: 3 },
})[props.mode])

const stage = ref<ReadingStage>(props.mode === 'daily' ? 'intro' : 'question')
const question = ref('')
const selected = ref<TarotCardData[]>([])
const result = ref<ReadingResponse | null>(null)
const errorMessage = ref('')
const clarification = ref('')
const inputMode = ref<'camera' | 'touch' | null>(null)
const cameraStatus = ref<'idle' | 'loading' | 'ready' | 'error'>('idle')
const yoloStatus = ref<'closed' | 'connecting' | 'open' | 'error'>('closed')
const lastGesture = ref('Waiting for movement')
const video = ref<HTMLVideoElement | null>(null)
const wheel = ref<InstanceType<typeof CardWheel> | null>(null)
let mediaPipe: MediaPipeGestureController | null = null
let yolo: YoloGestureClient | null = null
let yoloFrameTimer = 0

const canContinueQuestion = computed(() => props.mode === 'daily' || question.value.trim().length > 2)
const revealedCards = computed(() => {
  const cards = result.value?.cards?.length ? result.value.cards : selected.value
  return cards.map((card) => ({
    ...card,
    imageUrl: card.imageUrl || deck.find((item) => item.id === card.id)?.imageUrl || '',
  }))
})

function enterPermission(): void {
  if (!canContinueQuestion.value) return
  stage.value = 'permission'
}
function beginTouch(): void {
  inputMode.value = 'touch'
  stage.value = 'selecting'
}
async function beginCamera(): Promise<void> {
  inputMode.value = 'camera'
  cameraStatus.value = 'loading'
  stage.value = 'selecting'
  await nextTick()
  if (!video.value) return
  try {
    mediaPipe = new MediaPipeGestureController({ video: video.value, onGesture: handleGesture })
    await mediaPipe.start()
    cameraStatus.value = 'ready'
    connectYolo()
  } catch (error) {
    cameraStatus.value = 'error'
    errorMessage.value = error instanceof Error ? error.message : 'Camera could not be started.'
  }
}

function connectYolo(): void {
  const url = import.meta.env.VITE_GESTURE_WS_URL as string | undefined
  if (!url || !video.value) return
  yolo = new YoloGestureClient({
    url,
    onGesture: handleGesture,
    onStatus: (status) => { yoloStatus.value = status },
  })
  yolo.connect()

  const canvas = document.createElement('canvas')
  canvas.width = 480
  canvas.height = 360
  const context = canvas.getContext('2d')
  yoloFrameTimer = window.setInterval(() => {
    if (!context || !video.value || video.value.readyState < 2) return
    context.drawImage(video.value, 0, 0, canvas.width, canvas.height)
    canvas.toBlob((blob) => { if (blob) yolo?.sendFrame(blob) }, 'image/jpeg', .62)
  }, 240)
}

function handleGesture(event: GestureEvent): void {
  lastGesture.value = `${event.source} · ${event.gesture}`
  // MediaPipe owns continuous movement. YOLO is only allowed to supply discrete fallback actions.
  if (event.source === 'yolo' && event.action === 'rotate') return
  if (event.action === 'rotate') wheel.value?.rotateBy(event.delta ?? 0)
  if (event.action === 'shuffle') wheel.value?.shuffle()
  if (event.action === 'stop') wheel.value?.stop()
  if (event.action === 'select' || event.action === 'request_reading') wheel.value?.selectCentered()
  if (event.action === 'reset') resetReading()
}

function chooseCard(card: TarotCardData): void {
  if (stage.value !== 'selecting' || selected.value.some((item) => item.id === card.id)) return
  selected.value.push({ ...card, reversed: Math.random() > .5 })
  if (selected.value.length >= config.value.count) submitReading()
  else wheel.value?.shuffle()
}

async function submitReading(): Promise<void> {
  stage.value = 'drawing'
  await new Promise((resolve) => window.setTimeout(resolve, 1000))
  stage.value = 'submitting'
  try {
    const positions = props.mode === 'deep' ? ['Past influence', 'Present tension', 'Possible direction'] : []
    const payload = {
      question: props.mode === 'daily' ? null : question.value.trim(),
      spread_type: config.value.spread,
      cards: selected.value.map((card, index) => ({ id: card.id, reversed: card.reversed, position: positions[index] })),
    }
    result.value = await createTarotReading(payload)
    stage.value = result.value.status === 'awaiting_clarify' ? 'awaiting_clarify' : 'success'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'The reading could not be completed.'
    stage.value = 'error'
  }
}

async function submitClarification(): Promise<void> {
  if (!result.value?.clarify_session_id || !clarification.value.trim()) return
  stage.value = 'submitting'
  try {
    result.value = await clarifyTarotReading(result.value.clarify_session_id, clarification.value.trim())
    stage.value = 'success'
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Clarification failed.'
    stage.value = 'error'
  }
}

function resetReading(): void {
  selected.value = []
  result.value = null
  clarification.value = ''
  errorMessage.value = ''
  stage.value = props.mode === 'daily' ? 'intro' : 'question'
}

function teardown(): void {
  mediaPipe?.stop()
  mediaPipe = null
  yolo?.disconnect()
  yolo = null
  window.clearInterval(yoloFrameTimer)
}
onBeforeUnmount(teardown)
</script>

<template>
  <main class="reading" :class="[`reading--${mode}`, `stage--${stage}`]">
    <div class="reading__grain"></div>
    <div class="reading__cloud reading__cloud--one"></div>
    <div class="reading__cloud reading__cloud--two"></div>

    <header class="reading__header">
      <RouterLink class="reading__back" to="/home">← Home</RouterLink>
      <p>LUNAARC / {{ config.label }}</p>
      <span>{{ selected.length }} / {{ config.count }}</span>
    </header>

    <section v-if="stage === 'intro' || stage === 'question'" class="opening">
      <p class="eyebrow">{{ config.label }}</p>
      <h1>{{ config.title }}</h1>
      <p class="opening__subtitle">{{ config.subtitle }}</p>

      <div v-if="mode !== 'daily'" class="question-field">
        <label for="tarot-question">WHAT WOULD YOU LIKE TO ASK?</label>
        <textarea id="tarot-question" v-model="question" maxlength="280" placeholder="Write one honest question…"></textarea>
        <span>{{ question.length }}/280</span>
      </div>

      <button class="primary-action" :disabled="!canContinueQuestion" @click="enterPermission">
        Enter the reading <span>→</span>
      </button>
    </section>

    <section v-else-if="stage === 'permission'" class="permission">
      <p class="eyebrow">CHOOSE HOW TO MOVE</p>
      <h2>Your hands can guide the wheel,<br />but touch is equally complete.</h2>
      <div class="permission__choices">
        <button @click="beginCamera">
          <span class="permission__orb"></span>
          <strong>Move with your hand</strong>
          <small>MediaPipe motion + YOLO gesture fallback</small>
        </button>
        <button @click="beginTouch">
          <span class="permission__orb permission__orb--light"></span>
          <strong>Continue with touch</strong>
          <small>Drag, scroll, or tap the cards</small>
        </button>
      </div>
    </section>

    <section v-else-if="['selecting','drawing','submitting'].includes(stage)" class="ritual">
      <div class="ritual__copy">
        <p class="eyebrow">{{ question ? 'YOU ASKED' : 'TODAY' }}</p>
        <h2>{{ question || 'Let the day arrive before you name it.' }}</h2>
        <p v-if="stage === 'selecting'">Move slowly. Draw {{ config.count === 1 ? 'the card that holds your attention' : `${config.count - selected.length} more card${config.count - selected.length === 1 ? '' : 's'}` }}.</p>
        <p v-else>{{ stage === 'submitting' ? 'Your reading is taking shape…' : 'The chosen card is leaving the wheel…' }}</p>
      </div>

      <video v-show="inputMode === 'camera'" ref="video" class="camera-preview" muted playsinline></video>
      <div v-if="inputMode === 'camera'" class="gesture-status">
        <i :class="cameraStatus"></i>
        {{ cameraStatus === 'ready' ? lastGesture : cameraStatus }}
        <small>YOLO: {{ yoloStatus }}</small>
      </div>

      <CardWheel v-if="stage === 'selecting'" ref="wheel" :cards="deck" :back-url="backUrl" @select="chooseCard" />

      <div v-else class="chosen-cards">
        <TarotCard v-for="card in selected" :key="card.id" :card="card" :back-url="backUrl" :revealed="stage === 'submitting'" selected />
      </div>
    </section>

    <section v-else-if="stage === 'awaiting_clarify'" class="clarify">
      <p class="eyebrow">ONE MORE THREAD</p>
      <h2>{{ result?.clarify_prompt || 'A little more context will make the pattern clearer.' }}</h2>
      <p>{{ result?.summary }}</p>
      <textarea v-model="clarification" placeholder="Add what feels important…"></textarea>
      <button class="primary-action" :disabled="!clarification.trim()" @click="submitClarification">Continue <span>→</span></button>
    </section>

    <section v-else-if="stage === 'success' && result" class="result">
      <div class="result__heading">
        <p class="eyebrow">YOUR READING</p>
        <h1>{{ result.title }}</h1>
        <p>{{ result.summary }}</p>
      </div>
      <div class="result__cards" :class="{ 'is-three': revealedCards.length === 3 }">
        <article v-for="card in revealedCards" :key="card.id" class="result-card">
          <TarotCard :card="card" :back-url="backUrl" revealed />
          <div>
            <p class="eyebrow">{{ card.position || (card.reversed ? 'REVERSED' : 'UPRIGHT') }}</p>
            <h3>{{ card.name }}</h3>
            <p>{{ card.interpretation }}</p>
          </div>
        </article>
      </div>
      <aside class="advice"><span>ADVICE</span><p>{{ result.advice }}</p></aside>
      <div class="result__actions">
        <button @click="resetReading">Begin again</button>
        <RouterLink to="/home">Return home →</RouterLink>
      </div>
    </section>

    <section v-else-if="stage === 'error'" class="error-panel">
      <p class="eyebrow">THE THREAD BROKE</p>
      <h2>We could not complete this reading.</h2>
      <p>{{ errorMessage }}</p>
      <button class="primary-action" @click="resetReading">Try again <span>→</span></button>
    </section>
  </main>
</template>

<style scoped>
.reading { --ink:#f5f3e9; --blue:#11215b; min-height:100svh; position:relative; overflow:hidden; color:var(--ink); background:radial-gradient(circle at 68% 38%,#6578a7 0,#354b82 36%,#0c174a 76%,#050d32 100%); font-family:Inter,ui-sans-serif,system-ui,sans-serif; }
.reading::before { content:''; position:absolute; inset:0; background:linear-gradient(120deg,rgba(255,255,255,.04),transparent 42%),radial-gradient(circle at 50% 115%,rgba(183,205,255,.28),transparent 48%); pointer-events:none; }
.reading__grain { position:absolute; inset:0; opacity:.11; pointer-events:none; background-image:radial-gradient(rgba(255,255,255,.8) .7px,transparent .7px); background-size:8px 8px; mask-image:linear-gradient(to bottom,black,transparent 78%); }
.reading__cloud { position:absolute; border-radius:50%; filter:blur(48px); background:rgba(234,239,255,.15); }
.reading__cloud--one { width:34vw;height:20vw;left:-12vw;bottom:12vh; }
.reading__cloud--two { width:30vw;height:18vw;right:-8vw;top:18vh; }
.reading__header { position:relative; z-index:200; display:grid; grid-template-columns:1fr auto 1fr; align-items:center; padding:26px clamp(24px,4vw,72px); font-size:10px; letter-spacing:.18em; }
.reading__header p { margin:0; opacity:.72; }
.reading__header span { justify-self:end; opacity:.56; }
.reading__back { color:inherit; text-decoration:none; letter-spacing:.08em; }
.eyebrow { font-size:10px!important; letter-spacing:.22em; font-weight:700; opacity:.68; }
.opening,.permission,.clarify,.error-panel { position:relative; z-index:4; width:min(920px,calc(100% - 48px)); min-height:calc(100svh - 90px); margin:auto; display:flex; flex-direction:column; justify-content:center; align-items:flex-start; }
.opening h1,.result__heading h1 { max-width:960px; margin:18px 0; font-size:clamp(46px,7.5vw,112px); line-height:.91; letter-spacing:-.065em; font-weight:500; }
.opening__subtitle { font-size:clamp(16px,1.5vw,22px); opacity:.72; }
.question-field { width:min(720px,100%); margin-top:42px; padding:20px 0 10px; border-top:1px solid rgba(255,255,255,.26); border-bottom:1px solid rgba(255,255,255,.26); position:relative; }
.question-field label { font-size:9px;letter-spacing:.2em;opacity:.62; }
.question-field textarea,.clarify textarea { width:100%; min-height:90px; resize:none; border:0; outline:0; color:var(--ink); background:transparent; font:400 clamp(22px,3vw,42px)/1.2 inherit; padding:14px 0; }
.question-field textarea::placeholder,.clarify textarea::placeholder { color:rgba(255,255,255,.34); }
.question-field span { position:absolute; right:0; bottom:8px; font-size:9px; opacity:.45; }
.primary-action { margin-top:34px; min-width:210px; padding:15px 20px; display:flex; justify-content:space-between; border-radius:999px; border:1px solid rgba(255,255,255,.46); background:rgba(255,255,255,.1); color:inherit; backdrop-filter:blur(18px); cursor:pointer; }
.primary-action:disabled { opacity:.35;cursor:not-allowed; }
.permission h2,.clarify h2,.error-panel h2 { margin:14px 0 34px; font-size:clamp(38px,5vw,72px); letter-spacing:-.05em; line-height:.98; font-weight:500; }
.permission__choices { width:100%; display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px; }
.permission__choices button { min-height:220px;text-align:left;padding:30px;border-radius:32px;border:1px solid rgba(255,255,255,.3);background:rgba(246,245,237,.1);color:inherit;backdrop-filter:blur(26px);display:flex;flex-direction:column;gap:10px;cursor:pointer; }
.permission__choices strong { margin-top:auto;font-size:22px;font-weight:500; }
.permission__choices small { opacity:.58; }
.permission__orb { width:58px;height:58px;border-radius:50%;background:#7fa4f2;box-shadow:0 0 0 12px rgba(127,164,242,.12),0 0 45px rgba(127,164,242,.45); }
.permission__orb--light { background:#f4f1e8;box-shadow:0 0 0 12px rgba(255,255,255,.08); }
.ritual { position:absolute;inset:0; }
.ritual__copy { position:absolute;z-index:140;left:clamp(24px,6vw,110px);top:15vh;width:min(520px,60vw); }
.ritual__copy h2 { margin:12px 0;font-size:clamp(30px,4vw,62px);line-height:1;letter-spacing:-.045em;font-weight:500; }
.ritual__copy > p:last-child { opacity:.64; }
.camera-preview { position:absolute;z-index:160;right:28px;top:92px;width:150px;aspect-ratio:4/3;object-fit:cover;border-radius:22px;transform:scaleX(-1);opacity:.52;filter:saturate(.4) contrast(.9);border:1px solid rgba(255,255,255,.3); }
.gesture-status { position:absolute;z-index:161;right:28px;top:218px;width:150px;font-size:9px;letter-spacing:.08em;display:flex;align-items:center;gap:6px;opacity:.75; }
.gesture-status i { width:6px;height:6px;border-radius:50%;background:#f1cb75; }.gesture-status i.ready{background:#8dd7b0}.gesture-status i.error{background:#f28f8f}.gesture-status small{margin-left:auto;opacity:.55}
.chosen-cards { position:absolute;inset:0;z-index:90;display:flex;align-items:center;justify-content:center;gap:clamp(18px,4vw,64px);background:rgba(5,11,42,.28);backdrop-filter:blur(18px); }
.clarify p:not(.eyebrow),.error-panel p:not(.eyebrow){max-width:680px;opacity:.72;font-size:18px;line-height:1.7}.clarify textarea{max-width:720px;border-bottom:1px solid rgba(255,255,255,.3)}
.result { position:relative;z-index:5;min-height:100svh;padding:12vh clamp(24px,7vw,120px) 90px;background:#f2eee4;color:#223d82; }
.result__heading { max-width:960px; }.result__heading h1{font-size:clamp(48px,7vw,104px)}.result__heading>p:last-child{max-width:720px;font-size:18px;line-height:1.7;color:#566891}
.result__cards { margin-top:80px;display:grid;gap:80px; }.result-card{display:grid;grid-template-columns:auto minmax(0,620px);gap:48px;align-items:center}.result-card:nth-child(even){justify-content:end}.result-card h3{font-size:clamp(34px,4vw,62px);letter-spacing:-.04em;margin:8px 0}.result-card div>p:last-child{line-height:1.75;color:#60719a}.result__cards.is-three .result-card:nth-child(2){margin-left:10vw}.result__cards.is-three .result-card:nth-child(3){margin-left:20vw}
.advice { margin-top:100px;padding:36px 0;border-top:1px solid rgba(34,61,130,.22);border-bottom:1px solid rgba(34,61,130,.22);display:grid;grid-template-columns:180px 1fr;gap:30px}.advice span{font-size:10px;letter-spacing:.22em}.advice p{font-size:clamp(22px,3vw,38px);line-height:1.3;margin:0}.result__actions{margin-top:46px;display:flex;gap:24px}.result__actions button,.result__actions a{border:0;background:transparent;color:#223d82;text-decoration:none;font-weight:700;cursor:pointer}
@media(max-width:760px){.reading__header{grid-template-columns:1fr auto}.reading__header p{display:none}.permission__choices{grid-template-columns:1fr}.permission__choices button{min-height:160px}.ritual__copy{top:12vh;width:calc(100% - 48px)}.camera-preview{width:94px;top:auto;bottom:22px}.gesture-status{display:none}.result-card{grid-template-columns:1fr;gap:24px}.result__cards.is-three .result-card{margin-left:0}.advice{grid-template-columns:1fr}.opening h1{font-size:52px}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;animation-duration:.01ms!important;transition-duration:.01ms!important}}
</style>
