<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useDemoMode } from '../../composables/useDemoMode'
import { useSimulationStore } from '../../stores/simulation'
import { useTutorialStore } from '../../stores/tutorial'

const route = useRoute()
const { isDemoMode } = useDemoMode()
const simulationStore = useSimulationStore()
const tutorial = useTutorialStore()
const mobileMenuOpen = ref(false)
const helpMenuOpen = ref(false)
const helpMenuRef = ref(null)

function onClickOutsideHelp(e) {
  if (helpMenuRef.value && !helpMenuRef.value.contains(e.target)) {
    helpMenuOpen.value = false
  }
}

onMounted(() => document.addEventListener('click', onClickOutsideHelp))
onUnmounted(() => document.removeEventListener('click', onClickOutsideHelp))

const navLinks = computed(() => {
  return [
    { to: '/', label: 'Home', exact: true, tutorial: 'scenarios' },
    { to: '/simulations', label: 'Simulations', exact: false, showActiveDot: true, tutorial: 'simulations' },
    { to: '/settings', label: 'Settings', exact: false, tutorial: 'settings' },
  ]
})

watch(() => route.path, () => {
  mobileMenuOpen.value = false
})
</script>

<template>
  <nav data-tutorial="nav" class="bg-[var(--color-navy)] border-b border-white/10 px-4 md:px-6 py-3 relative">
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-6">
        <router-link to="/" class="flex items-center gap-2 text-white no-underline">
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-label="Intercom logo">
            <rect width="28" height="28" rx="6" fill="var(--color-primary)"/>
            <path d="M7 10.5C7 10.2239 7.22386 10 7.5 10H8.5C8.77614 10 9 10.2239 9 10.5V17.5C9 17.7761 8.77614 18 8.5 18H7.5C7.22386 18 7 17.7761 7 17.5V10.5Z" fill="white"/>
            <path d="M10.5 8.5C10.5 8.22386 10.7239 8 11 8H12C12.2761 8 12.5 8.22386 12.5 8.5V19.5C12.5 19.7761 12.2761 20 12 20H11C10.7239 20 10.5 19.7761 10.5 19.5V8.5Z" fill="white"/>
            <path d="M15.5 8.5C15.5 8.22386 15.7239 8 16 8H17C17.2761 8 17.5 8.22386 17.5 8.5V19.5C17.5 19.7761 17.2761 20 17 20H16C15.7239 20 15.5 19.7761 15.5 19.5V8.5Z" fill="white"/>
            <path d="M19 10.5C19 10.2239 19.2239 10 19.5 10H20.5C20.7761 10 21 10.2239 21 10.5V17.5C21 17.7761 20.7761 18 20.5 18H19.5C19.2239 18 19 17.7761 19 17.5V10.5Z" fill="white"/>
            <path d="M8 20.5C9.5 22 11.5 23 14 23C16.5 23 18.5 22 20 20.5" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
          </svg>
          <span class="text-sm font-semibold tracking-tight">MiroFish</span>
          <span class="text-xs text-white/40 ml-1 hidden sm:inline">GTM Demo</span>
          <span
            v-if="isDemoMode"
            class="ml-2 text-xs font-semibold text-white bg-[#2068FF] px-2 py-0.5 rounded-full"
          >DEMO</span>
        </router-link>

        <div class="hidden md:flex items-center gap-1">
          <router-link
            v-for="link in navLinks"
            :key="link.to"
            :to="link.to"
            :exact="link.exact"
            :data-tutorial="link.tutorial"
            class="nav-link"
            :class="{ 'nav-link--exact': link.exact }"
          >
            <span class="flex items-center gap-1.5">
              {{ link.label }}
              <span
                v-if="link.showActiveDot && simulationStore.isActive"
                class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"
              ></span>
            </span>
          </router-link>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <!-- Help menu -->
        <div ref="helpMenuRef" class="relative" data-tutorial="reports">
          <button
            class="hidden sm:flex items-center gap-1 text-xs text-white/50 hover:text-white transition-colors cursor-pointer"
            @click.stop="helpMenuOpen = !helpMenuOpen"
            aria-label="Help menu"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="12" cy="12" r="10" />
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
            <span>Help</span>
          </button>

          <Transition
            enter-active-class="transition duration-150 ease-out"
            enter-from-class="opacity-0 -translate-y-1"
            enter-to-class="opacity-100 translate-y-0"
            leave-active-class="transition duration-100 ease-in"
            leave-from-class="opacity-100 translate-y-0"
            leave-to-class="opacity-0 -translate-y-1"
          >
            <div v-if="helpMenuOpen" class="absolute top-full right-0 mt-2 w-48 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg shadow-lg py-1 z-50">
              <button
                class="w-full text-left px-3 py-2 text-sm text-[var(--color-text)] hover:bg-[var(--color-border)] transition-colors cursor-pointer"
                @click="tutorial.startWelcomeTour(); helpMenuOpen = false"
              >
                Welcome Tour
              </button>
              <button
                class="w-full text-left px-3 py-2 text-sm text-[var(--color-text)] hover:bg-[var(--color-border)] transition-colors cursor-pointer"
                @click="tutorial.startWalkthrough(); helpMenuOpen = false"
              >
                Guided Walkthrough
              </button>
              <button
                class="w-full text-left px-3 py-2 text-sm text-[var(--color-text)] hover:bg-[var(--color-border)] transition-colors cursor-pointer"
                @click="tutorial.toggleShortcutRef(); helpMenuOpen = false"
              >
                Keyboard Shortcuts
                <span class="text-xs text-[var(--color-text-muted)] ml-1">Ctrl+/</span>
              </button>
            </div>
          </Transition>
        </div>

        <div class="hidden sm:flex items-center gap-2 text-xs text-white/40">
          <span class="w-2 h-2 rounded-full bg-green-500"></span>
          <span>Local</span>
        </div>

        <button
          @click="mobileMenuOpen = !mobileMenuOpen"
          class="md:hidden text-white/60 hover:text-white transition-colors"
          :aria-expanded="mobileMenuOpen"
          aria-label="Toggle navigation menu"
        >
          <svg v-if="!mobileMenuOpen" width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zm0 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd"/>
          </svg>
          <svg v-else width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Mobile menu dropdown -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 -translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-2"
    >
      <div v-if="mobileMenuOpen" class="md:hidden absolute top-full left-0 right-0 bg-[#050505] border-b border-white/10 z-50">
        <div class="px-4 py-3 space-y-1">
          <router-link
            v-for="link in navLinks"
            :key="link.to"
            :to="link.to"
            class="flex items-center gap-1.5 px-3 py-2.5 text-sm text-white/70 hover:text-white hover:bg-white/5 rounded-lg transition-colors no-underline"
          >
            {{ link.label }}
            <span
              v-if="link.showActiveDot && simulationStore.isActive"
              class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"
            ></span>
          </router-link>
        </div>
        <div class="px-4 pb-3 flex items-center gap-2 text-xs text-white/40">
          <span class="w-2 h-2 rounded-full bg-green-500"></span>
          Connected
        </div>
      </div>
    </Transition>
  </nav>
</template>

<style scoped>
.nav-link {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.6);
  text-decoration: none;
  padding: 0.25rem 0.75rem;
  border-radius: var(--radius-sm);
  transition: color var(--transition-fast), background-color var(--transition-fast);
}
.nav-link:hover {
  color: white;
  background-color: rgba(255, 255, 255, 0.08);
}
.nav-link.router-link-active {
  color: white;
  background-color: rgba(255, 255, 255, 0.12);
}
.nav-link--exact.router-link-active:not(.router-link-exact-active) {
  color: rgba(255, 255, 255, 0.6);
  background-color: transparent;
}
.nav-link--exact.router-link-exact-active {
  color: white;
  background-color: rgba(255, 255, 255, 0.12);
}
</style>
