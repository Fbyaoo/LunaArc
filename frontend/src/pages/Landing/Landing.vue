<template>

<div class="landing">


<div
class="background"
/>


<CurtainLayer
v-if="stage==='landing'"
/>



<EyePortal

v-if="stage==='landing'"

@enter="openPortal"

/>



<SceneTransition

ref="transition"

/>



<OpenScene

v-if="stage==='opening'"

@join="showAuth"

/>



<AuthPortal

v-if="stage==='auth'"

/>


</div>


</template>



<script setup lang="ts">

import {
ref
} from "vue"



import CurtainLayer
from "@/components/landing/CurtainLayer.vue"


import EyePortal
from "@/components/landing/EyePortal.vue"


import SceneTransition
from "@/components/landing/SceneTransition.vue"


import OpenScene
from "@/components/landing/OpenScene.vue"


import AuthPortal
from "@/components/landing/AuthPortal.vue"



const stage=
ref<
'landing'|
'opening'|
'auth'
>('landing')



const transition=
ref<any>(null)



function openPortal(){


console.log("eye enter")


// 启动转场

transition.value?.startTransition()



// 等待转场完成

setTimeout(()=>{


stage.value="opening"



},1200)



}



function showAuth(){


stage.value="auth"



}



</script>



<style scoped>


.landing{


position:fixed;


inset:0;


overflow:hidden;


background:#06153F;


}



.background{


position:absolute;


inset:0;


background:

url("@/assets/landing/landing-bg.webp")

center/cover;


z-index:-1;


}



</style>