<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppNav from './AppNav.vue'
import AppFooter from './AppFooter.vue'
import MobileNav from './MobileNav.vue'

const route = useRoute()
const isLanding = computed(() => route.name === 'landing')
</script>

<template>
  <div class="min-h-screen flex flex-col bg-[var(--color-bg)]">
    <AppNav />
    <main class="flex-1" :class="{ 'pb-16 md:pb-0': !isLanding }">
      <slot />
    </main>
    <AppFooter v-if="!isLanding" />
    <MobileNav v-if="!isLanding" />
  </div>
</template>
