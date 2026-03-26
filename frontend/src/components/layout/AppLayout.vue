<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import AppNav from './AppNav.vue'
import AppFooter from './AppFooter.vue'
import MobileNav from './MobileNav.vue'
import GuestBanner from './GuestBanner.vue'
import AiAnalyst from '../insights/AiAnalyst.vue'

const route = useRoute()
const auth = useAuthStore()
const hideChrome = computed(() => route.meta.hideNav === true)
const isLanding = computed(() => route.name === 'landing')
const showFooter = computed(() => !hideChrome.value && !isLanding.value)
</script>

<template>
  <div class="min-h-screen flex flex-col bg-[var(--color-bg)]">
    <a href="#main-content" class="skip-to-main">Skip to main content</a>
    <AppNav v-if="!hideChrome" />
    <GuestBanner v-if="auth.isGuest" />
    <main id="main-content" class="flex-1" :class="{ 'pb-16 md:pb-0': !isLanding }">
      <slot />
    </main>
    <AppFooter v-if="showFooter" />
    <MobileNav v-if="showFooter" />
    <AiAnalyst :context="{ page: route.name }" />
  </div>
</template>
