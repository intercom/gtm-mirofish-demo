<script setup>
import AppNav from './components/layout/AppNav.vue'
import AppFooter from './components/layout/AppFooter.vue'
import { useTheme } from './composables/useTheme.js'

useTheme()
</script>

<template>
  <div class="min-h-screen flex flex-col bg-(--color-bg) text-(--color-text) transition-colors duration-300">
    <AppNav />
    <main class="flex-1">
      <router-view />
    </main>
    <AppFooter />
  </div>
</template>
