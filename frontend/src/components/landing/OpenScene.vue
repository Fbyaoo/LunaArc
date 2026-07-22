<template>

<div class="open-scene">


<div class="scene-bg"></div>



<div
class="content about"
:class="{hide:showWide}"
>


<div class="tag">

LUNAARC

<span>
MIND EXPLORATION / AI TAROT
</span>

</div>



<h1>

ABOUT ME

</h1>


<h2>

Click the eye and Open your mind.

</h2>


<p>

· Relaxation is happiness. All for reference only.

</p>



</div>





<div
class="content wide"
:class="{show:showWide}"
>



<div class="tag">

LUNAARC

<span>
MIND EXPLORATION / AI TAROT
</span>

</div>



<h1>

OPEN WIDE

</h1>



<h2>

Ready to dig into your universe.

</h2>



<p>

· Relaxation is happiness. All for reference only.

</p>



<button

class="join-button"

@click="join"

>

Join ->

</button>



</div>




</div>


</template>




<script setup lang="ts">


import {

ref,

onMounted,

onBeforeUnmount

}

from "vue"



const emit=

defineEmits<{

join:[]

}>()



const showWide=

ref(false)



let timer:number



onMounted(()=>{


timer=

window.setTimeout(()=>{


showWide.value=true



},5000)



})



onBeforeUnmount(()=>{


clearTimeout(timer)



})



function join(){


emit("join")

}


</script>




<style scoped>


.open-scene{


position:absolute;


inset:0;


overflow:hidden;


font-family:

Arial,
Helvetica,
sans-serif;


}



/* 背景景深 */

.scene-bg{


position:absolute;


inset:0;



background:

url("@/assets/landing/landing-bg.webp")

center/cover;



animation:

cameraDepth 5s ease forwards;


}




@keyframes cameraDepth{


0%{


transform:

scale(1);



filter:

blur(0px);



}


100%{


transform:

scale(1.08);



filter:

blur(5px);



}



}




.content{


position:absolute;



right:12%;



width:520px;



text-align:left;



color:white;



transition:

all 1.8s cubic-bezier(.22,1,.36,1);



}




/* ABOUT ME */

.about{


top:38%;



opacity:1;



transform:

translateY(0);



}




.about.hide{


opacity:0;



transform:

translateY(80px);



}




/* OPEN WIDE */

.wide{


top:55%;



opacity:0;



transform:

translateY(80px);



}




.wide.show{


opacity:1;



transform:

translateY(0);



}




.tag{


font-size:

16px;



font-weight:

400;



color:#F5C542;



margin-bottom:18px;



letter-spacing:.5px;



}




.tag span{


margin-left:25px;



}



h1{


margin:0;



font-size:

78px;



font-weight:

900;



line-height:.95;



letter-spacing:2px;



color:white;



}




h2{


margin:

20px 0;



font-size:

34px;



font-weight:

700;



line-height:

1.2;



color:white;



}



p{


font-size:

15px;



font-weight:

400;



color:white;



}




.join-button{


margin-top:

30px;



width:

145px;



height:

55px;



border-radius:

40px;



border:

1px solid rgba(255,255,255,.45);



background:

rgba(255,255,255,.15);



backdrop-filter:

blur(20px);



color:white;



font-size:

16px;



font-weight:

700;



cursor:pointer;



transition:.4s;



}




.join-button:hover{


background:

rgba(255,255,255,.28);



transform:

translateY(-5px);



}



</style>