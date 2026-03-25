<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import AppNav from './AppNav.vue'
import AppFooter from './AppFooter.vue'
import GuestBanner from './GuestBanner.vue'

const route = useRoute()
const auth = useAuthStore()
const showFooter = computed(() => route.name !== 'landing')
</script>

<template>
  <div class="min-h-screen flex flex-col bg-[var(--color-bg)]">
    <AppNav />
    <GuestBanner v-if="auth.isGuest" />
    <main class="flex-1">
      <slot />
    </main>
    <AppFooter v-if="showFooter" />
  </div>
</template>
