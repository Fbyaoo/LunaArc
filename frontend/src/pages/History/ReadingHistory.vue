<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getReadings, setReadingSaved } from '@/api/readings'
import type { ReadingSummaryItem } from '@/types/reading'

const router = useRouter()
const readings = ref<ReadingSummaryItem[]>([])
const isLoading = ref(true)
const errorMessage = ref('')

async function load(): Promise<void> {
  isLoading.value = true
  try { readings.value = (await getReadings()).items }
  catch (e) { errorMessage.value = e instanceof Error ? e.message : 'Could not load your readings.' }
  finally { isLoading.value = false }
}

function open(id: string): void { void router.push({ name: 'reading-detail', params: { readingId: id } }) }
async function toggle(reading: ReadingSummaryItem): Promise<void> {
  const old = reading.saved; reading.saved = !old
  try { await setReadingSaved(reading.id, reading.saved) } catch { reading.saved = old }
}
onMounted(() => void load())
</script>

<template>
  <main class="page">
    <header><p>YOUR SPACE</p><h1>Reading History</h1><span>Return to what stayed with you.</span></header>
    <p v-if="isLoading" class="state">Gathering your reflections…</p>
    <section v-else-if="errorMessage" class="state"><p>{{ errorMessage }}</p><button @click="load">Try again</button></section>
    <section v-else-if="!readings.length" class="state"><p>No readings yet.</p><RouterLink to="/reading/daily">Begin with Daily Fortune</RouterLink></section>
    <section v-else class="grid">
      <article v-for="r in readings" :key="r.id" @click="open(r.id)">
        <small>{{ r.spread_type.replace('_',' ') }}</small><h2>{{ r.title }}</h2><p>{{ r.summary }}</p>
        <button @click.stop="toggle(r)">{{ r.saved ? 'Saved' : 'Save' }}</button>
      </article>
    </section>
  </main>
</template>

<style scoped>
.page{min-height:100vh;padding:84px clamp(24px,7vw,110px);background:#f5f0e7;color:#294887}header p{margin:0;font-size:.68rem;font-weight:700;letter-spacing:.18em}header h1{margin:12px 0;font-size:clamp(3rem,7vw,7rem);font-weight:450;letter-spacing:-.065em}header span,.state{color:#8392b0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:18px;margin-top:56px}.grid article{min-height:240px;display:flex;flex-direction:column;padding:26px;border:1px solid rgba(70,92,140,.12);border-radius:24px;background:rgba(255,255,255,.56);cursor:pointer}.grid small{color:#8a99b7;text-transform:uppercase}.grid h2{margin:32px 0 12px}.grid p{color:#7182a3;line-height:1.6}.grid button{align-self:flex-start;margin-top:auto;border:0;background:transparent;color:#3157a2;cursor:pointer}.state{margin-top:80px}.state a,.state button{color:#3157a2}
</style>
