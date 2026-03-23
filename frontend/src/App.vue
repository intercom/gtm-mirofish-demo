<script setup>
import AppLayout from './components/layout/AppLayout.vue'
import { useTheme } from './composables/useTheme'

useTheme()
</script>

<template>
  <AppLayout>
    <router-view v-slot="{ Component }">
      <Transition name="page" mode="out-in">
        <component :is="Component" />
      </Transition>
    </router-view>
  </AppLayout>
</template>
