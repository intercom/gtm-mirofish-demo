<script setup>
import AppNav from './components/layout/AppNav.vue'
import AppFooter from './components/layout/AppFooter.vue'
import ToastContainer from './components/ui/ToastContainer.vue'
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <AppNav />
    <main class="flex-1">
      <router-view />
    </main>
    <AppFooter />
    <ToastContainer />
  </div>
</template>
