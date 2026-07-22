<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <RouterView v-slot="{ Component, route }">
    <Transition
      name="page-fade"
      mode="out-in"
    >
      <component
        :is="Component"
        :key="route.path"
      />
    </Transition>
  </RouterView>
</template>

<style>
#app {
  min-height: 100vh;
}

.page-fade-enter-active,
.page-fade-leave-active {
  transition:
    opacity 520ms ease,
    filter 520ms ease,
    transform 620ms cubic-bezier(.22, .8, .22, 1);
}

.page-fade-enter-from {
  opacity: 0;
  filter: blur(8px);
  transform: scale(1.008);
}

.page-fade-leave-to {
  opacity: 0;
  filter: blur(6px);
  transform: scale(.995);
}

@media (prefers-reduced-motion: reduce) {
  .page-fade-enter-active,
  .page-fade-leave-active {
    transition-duration: .01ms;
  }
}
</style>