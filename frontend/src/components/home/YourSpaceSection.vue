<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getRecentReadings, setReadingSaved } from '@/api/readings'
import type { ReadingSummaryItem } from '@/types/reading'

const router = useRouter()
const readings = ref<ReadingSummaryItem[]>([])
const isLoading = ref(true)
const errorMessage = ref('')
const savingIds = ref<Set<string>>(new Set())
const hasReadings = computed(() => readings.value.length > 0)

function formatType(type: ReadingSummaryItem['spread_type']): string {
  return ({ daily_card: 'Daily Fortune', single_card: 'Quick Question', three_card: 'Deep Reading' })[type]
}

function formatDate(value: string): string {
  const date = new Date(value)
  return new Intl.DateTimeFormat('en', {
    month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', hour12: false,
  }).format(date)
}

async function loadReadings(): Promise<void> {
  isLoading.value = true
  errorMessage.value = ''
  try {
    readings.value = (await getRecentReadings(3)).items
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : 'Your reflections could not be reached.'
  } finally {
    isLoading.value = false
  }
}

function enterGuide(): void { void router.push({ name: 'ai-guide' }) }
function viewAll(): void { void router.push({ name: 'reading-history' }) }
function openReading(id: string): void {
  void router.push({ name: 'reading-detail', params: { readingId: id } })
}

async function toggleSaved(event: MouseEvent, reading: ReadingSummaryItem): Promise<void> {
  event.stopPropagation()
  if (savingIds.value.has(reading.id)) return

  const original = reading.saved
  reading.saved = !reading.saved
  savingIds.value = new Set(savingIds.value).add(reading.id)

  try {
    await setReadingSaved(reading.id, reading.saved)
  } catch {
    reading.saved = original
  } finally {
    const next = new Set(savingIds.value)
    next.delete(reading.id)
    savingIds.value = next
  }
}

onMounted(() => void loadReadings())
</script>

<template>
  <section class="your-space" aria-labelledby="your-space-title">
    <div class="content">
      <header class="heading">
        <p>YOUR SPACE</p>
        <h2 id="your-space-title">Return to the thoughts that stayed<br />with you.</h2>
      </header>

      <div class="grid">
        <article class="panel guide" tabindex="0" @click="enterGuide" @keydown.enter="enterGuide">
          <div>
            <p class="eyebrow">AI TAROT GUIDE</p>
            <h3>Talk through what the cards brought up.</h3>
            <p class="copy">LunaArc remembers the context of your current reading and helps you reflect without rushing toward an answer.</p>
          </div>
          <button type="button" @click.stop="enterGuide"><span>Enter your guide</span><span>→</span></button>
        </article>

        <article class="panel readings">
          <div class="panel-head">
            <div><p class="eyebrow">RECENT READINGS</p><h3>Your last reflections</h3></div>
            <button class="view-all" type="button" @click="viewAll">View all</button>
          </div>

          <div v-if="isLoading" class="state">Gathering your reflections…</div>
          <div v-else-if="errorMessage" class="state">
            <p>{{ errorMessage }}</p><button type="button" @click="loadReadings">Try again</button>
          </div>
          <div v-else-if="!hasReadings" class="state">
            <p>Nothing has stayed here yet.</p>
            <RouterLink to="/reading/daily">Begin your first reading</RouterLink>
          </div>
          <div v-else class="list">
            <article v-for="reading in readings" :key="reading.id" class="row" tabindex="0" @click="openReading(reading.id)" @keydown.enter="openReading(reading.id)">
              <span class="symbol">✦</span>
              <div class="row-copy">
                <p>{{ formatType(reading.spread_type) }} · {{ formatDate(reading.created_at) }}</p>
                <h4>{{ reading.title }}</h4>
                <span>{{ reading.summary }}</span>
              </div>
              <button type="button" :disabled="savingIds.has(reading.id)" @click="toggleSaved($event, reading)">
                {{ reading.saved ? 'Saved' : 'Save' }}
              </button>
            </article>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>

<style scoped>
.your-space{position:relative;min-height:100vh;min-height:100svh;overflow:hidden;scroll-snap-align:start;background:linear-gradient(rgba(17,42,94,.28),rgba(17,42,94,.28)),url('@/assets/home/home-checkerboard.png') center/cover no-repeat}.content{width:min(1160px,calc(100% - 64px));margin:0 auto;padding:clamp(84px,10vh,132px) 0 94px}.heading{color:#fff}.heading>p,.eyebrow{margin:0 0 12px;font-size:.68rem;font-weight:700;letter-spacing:.18em}.heading>p{color:rgba(255,255,255,.75)}.heading h2{margin:0;font-size:clamp(2.2rem,4.2vw,4.4rem);font-weight:450;line-height:.98;letter-spacing:-.055em}.grid{display:grid;grid-template-columns:minmax(300px,.78fr) minmax(520px,1.32fr);gap:24px;margin-top:clamp(58px,8vh,88px)}.panel{border:1px solid rgba(255,255,255,.68);border-radius:28px;background:rgba(248,247,242,.86);box-shadow:0 30px 80px rgba(12,31,74,.16);backdrop-filter:blur(22px)}.guide{min-height:320px;display:flex;flex-direction:column;justify-content:flex-end;padding:34px;cursor:pointer;transition:transform .26s ease}.guide:hover{transform:translateY(-5px)}.eyebrow{color:#7890c6}.panel h3{margin:0;color:#2f4f98;font-size:clamp(1.3rem,2vw,2rem);font-weight:500;line-height:1.08}.copy{margin:18px 0 0;color:#7890b7;font-size:.88rem;line-height:1.65}.guide button{display:flex;justify-content:space-between;margin-top:34px;padding:14px 16px;border:0;border-radius:13px;background:rgba(255,255,255,.68);color:#3155a1;cursor:pointer}.readings{min-height:320px;padding:28px 30px 24px}.panel-head{display:flex;justify-content:space-between;gap:24px;padding-bottom:22px;border-bottom:1px solid rgba(60,84,135,.1)}.view-all,.state button{border:0;background:transparent;color:#7288b8;cursor:pointer}.row{display:grid;grid-template-columns:34px minmax(0,1fr) auto;gap:14px;align-items:center;min-height:82px;padding:13px 12px;border-bottom:1px solid rgba(58,81,129,.09);border-radius:16px;cursor:pointer}.row:hover{background:rgba(255,255,255,.58)}.symbol{display:grid;width:28px;height:28px;place-items:center;border-radius:50%;background:rgba(76,107,171,.09);color:#5f7dc0}.row-copy{min-width:0}.row-copy p{margin:0 0 4px;color:#9ba8c1;font-size:.61rem}.row-copy h4{margin:0;overflow:hidden;color:#2a4a92;font-size:.88rem;text-overflow:ellipsis;white-space:nowrap}.row-copy span{display:block;margin-top:5px;overflow:hidden;color:#8695b3;font-size:.69rem;text-overflow:ellipsis;white-space:nowrap}.row>button{min-width:50px;padding:6px 9px;border:0;border-radius:999px;background:rgba(83,109,166,.08);color:#7186b4;cursor:pointer}.state{min-height:230px;display:grid;place-content:center;gap:10px;text-align:center;color:#8090af}.state a{color:#3155a1}@media(max-width:980px){.content{width:min(760px,calc(100% - 40px))}.grid{grid-template-columns:1fr}}@media(max-width:640px){.content{width:min(100% - 28px,560px)}.heading h2 br{display:none}.row{grid-template-columns:30px minmax(0,1fr)}.row>button{grid-column:2;justify-self:start}}@media(prefers-reduced-motion:reduce){.guide{transition:none}}
</style>
