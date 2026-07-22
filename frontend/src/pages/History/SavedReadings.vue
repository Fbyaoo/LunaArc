<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getReadings, setReadingSaved } from '@/api/readings'
import type { ReadingSummaryItem } from '@/types/reading'
const router=useRouter();const readings=ref<ReadingSummaryItem[]>([]);const loading=ref(true);const error=ref('')
async function load(){loading.value=true;try{readings.value=(await getReadings(true)).items}catch(e){error.value=e instanceof Error?e.message:'Could not load saved readings.'}finally{loading.value=false}}
function open(id:string){void router.push({name:'reading-detail',params:{readingId:id}})}
async function remove(r:ReadingSummaryItem){try{await setReadingSaved(r.id,false);readings.value=readings.value.filter(x=>x.id!==r.id)}catch(e){error.value=e instanceof Error?e.message:'Could not update this reading.'}}
onMounted(()=>void load())
</script>
<template><main class="page"><header><p>YOUR SPACE</p><h1>Saved Readings</h1><span>Keep close what still speaks to you.</span></header><p v-if="loading" class="state">Opening your saved reflections…</p><section v-else-if="error" class="state"><p>{{error}}</p><button @click="load">Try again</button></section><section v-else-if="!readings.length" class="state"><p>You have not saved a reading yet.</p><RouterLink to="/history">Visit Reading History</RouterLink></section><section v-else class="list"><article v-for="r in readings" :key="r.id" @click="open(r.id)"><div><small>{{r.spread_type.replace('_',' ')}}</small><h2>{{r.title}}</h2><p>{{r.summary}}</p></div><button @click.stop="remove(r)">Remove</button></article></section></main></template>
<style scoped>.page{min-height:100vh;padding:84px clamp(24px,7vw,110px);background:linear-gradient(rgba(17,40,90,.22),rgba(17,40,90,.4)),url('@/assets/home/home-checkerboard.png') center/cover fixed;color:#fff}header p{margin:0;font-size:.68rem;font-weight:700;letter-spacing:.18em}header h1{margin:12px 0;font-size:clamp(3rem,7vw,7rem);font-weight:450;letter-spacing:-.065em}header span{color:rgba(255,255,255,.67)}.list{display:grid;gap:14px;margin-top:54px}.list article{display:flex;justify-content:space-between;gap:24px;padding:26px 28px;border:1px solid rgba(255,255,255,.55);border-radius:24px;background:rgba(246,246,242,.84);color:#294887;backdrop-filter:blur(18px);cursor:pointer}.list small{color:#8493b1;text-transform:uppercase}.list p{color:#7384a5}.list button{align-self:flex-start;border:0;background:transparent;color:#3157a2;cursor:pointer}.state{margin-top:70px}.state a,.state button{color:inherit}</style>
