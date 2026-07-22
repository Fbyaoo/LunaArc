<template>


<div

class="transition-layer"

:class="{active}"

>


</div>


</template>



<script setup lang="ts">


import {
ref
}
from "vue"



const active=
ref(false)



function startTransition(){


active.value=true



setTimeout(()=>{


active.value=false



},1400)



}



defineExpose({

startTransition

})


</script>




<style scoped>


.transition-layer{


position:absolute;


inset:0;



background:

rgba(8,18,55,.25);



backdrop-filter:

blur(0px);



opacity:0;



pointer-events:none;



z-index:100;



transition:

all 1.2s ease;



}



.transition-layer.active{


opacity:1;



backdrop-filter:

blur(12px);



}


</style>