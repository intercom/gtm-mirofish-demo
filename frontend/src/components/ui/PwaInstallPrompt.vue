<script setup>
import { ref, watch } from 'vue'
import { usePwaInstall } from '../../composables/usePwaInstall'

const { canInstall, isInstalled, wasDismissed, promptInstall, dismiss } = usePwaInstall()

const visible = ref(false)
const installing = ref(false)

watch(
  () => canInstall.value && !isInstalled.value && !wasDismissed.value,
  (show) => {
    if (show) {
      // Small delay so the banner doesn't flash on page load
      setTimeout(() => { visible.value = true }, 2000)
    } else {
      visible.value = false
    }
  },
  { immediate: true },
)

async function handleInstall() {
  installing.value = true
  await promptInstall()
  installing.value = false
}

function handleDismiss() {
  visible.value = false
  dismiss()
}
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-all duration-300 ease-out"
      leave-active-class="transition-all duration-200 ease-in"
      enter-from-class="translate-y-full opacity-0"
      enter-to-class="translate-y-0 opacity-100"
      leave-from-class="translate-y-0 opacity-100"
      leave-to-class="translate-y-full opacity-0"
    >
      <div
        v-if="visible"
        class="fixed bottom-4 left-4 right-4 sm:left-auto sm:right-4 sm:w-[380px] z-[9998] rounded-xl shadow-lg border border-white/10 bg-[#050505] text-white p-4"
      >
        <div class="flex items-start gap-3">
          <img
            src="/pwa-192x192.png"
            alt="MiroFish"
            class="w-10 h-10 rounded-lg shrink-0"
          />
          <div class="flex-1 min-w-0">
            <p class="text-sm font-semibold leading-tight">Install MiroFish</p>
            <p class="text-xs text-white/60 mt-0.5">
              Add to your home screen for quick access and offline use.
            </p>
          </div>
          <button
            @click="handleDismiss"
            class="shrink-0 text-white/40 hover:text-white/80 text-lg leading-none cursor-pointer p-1 -mt-1 -mr-1"
            aria-label="Dismiss"
          >
            &times;
          </button>
        </div>
        <div class="flex gap-2 mt-3">
          <button
            @click="handleDismiss"
            class="flex-1 text-xs font-medium py-2 px-3 rounded-lg bg-white/10 hover:bg-white/15 text-white/70 cursor-pointer transition-colors"
          >
            Not now
          </button>
          <button
            @click="handleInstall"
            :disabled="installing"
            class="flex-1 text-xs font-semibold py-2 px-3 rounded-lg bg-[#2068FF] hover:bg-[#1a5ae0] text-white cursor-pointer transition-colors disabled:opacity-50"
          >
            {{ installing ? 'Installing...' : 'Install' }}
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
