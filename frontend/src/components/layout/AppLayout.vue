<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppNav from './AppNav.vue'
import AppFooter from './AppFooter.vue'
import MobileNav from './MobileNav.vue'

const route = useRoute()
const hideChrome = computed(() => route.meta.hideNav === true)
const isLanding = computed(() => route.name === 'landing')
const showFooter = computed(() => !hideChrome.value && !isLanding.value)
</script>

<template>
  <div class="min-h-screen flex flex-col bg-[var(--color-bg)]">
    <AppNav v-if="!hideChrome" />
    <main class="flex-1" :class="{ 'pb-16 md:pb-0': !isLanding }">
      <slot />
    </main>
    <AppFooter v-if="showFooter" />
    <MobileNav v-if="showFooter" />
  </div>
</template>
