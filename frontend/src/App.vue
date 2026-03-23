<script setup>
import { watch } from 'vue'
import { useRoute } from 'vue-router'
import AppLayout from './components/layout/AppLayout.vue'
import ToastContainer from './components/ui/ToastContainer.vue'
import { useTheme } from './composables/useTheme'

const route = useRoute()
const { setRouteDefault } = useTheme()

watch(() => route.name, (name) => {
  setRouteDefault(name === 'landing' ? 'dark' : 'light')
}, { immediate: true })
</script>

<template>
  <AppLayout>
    <router-view v-slot="{ Component }">
      <Transition name="page" mode="out-in">
        <component :is="Component" />
      </Transition>
    </router-view>
  </AppLayout>
  <ToastContainer />
</template>
