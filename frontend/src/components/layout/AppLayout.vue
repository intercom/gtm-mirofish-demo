<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppNav from './AppNav.vue'
import AppFooter from './AppFooter.vue'

const route = useRoute()
const showFooter = computed(() => route.name !== 'landing')
</script>

<template>
  <div class="min-h-screen flex flex-col bg-[var(--color-bg)]">
    <a href="#main-content" class="skip-to-main">Skip to main content</a>
    <AppNav />
    <main id="main-content" class="flex-1">
      <slot />
    </main>
    <AppFooter v-if="showFooter" />
  </div>
</template>
