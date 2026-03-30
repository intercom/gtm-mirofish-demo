<script setup>
import { ref, computed } from 'vue'
import { getHelpContent } from '../../data/help-content'

const props = defineProps({
  helpKey: { type: String, required: true },
  position: { type: String, default: 'top' },
})

const isOpen = ref(false)
const entry = computed(() => getHelpContent(props.helpKey))

function toggle() {
  isOpen.value = !isOpen.value
}

function close() {
  isOpen.value = false
}
</script>

<template>
  <span class="contextual-help-wrapper" v-if="entry">
    <button
      class="contextual-help-trigger"
      :aria-label="`Learn about ${entry.title}`"
      @click.stop="toggle"
    >
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10" />
        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
      </svg>
    </button>

    <Transition name="help-pop">
      <div
        v-if="isOpen"
        class="contextual-help-popover"
        :class="`contextual-help-popover--${position}`"
        @click.stop
      >
        <div class="flex items-center justify-between mb-1.5">
          <h4 class="text-xs font-bold text-[var(--color-text)]">{{ entry.title }}</h4>
          <button
            class="text-[var(--color-text-muted)] hover:text-[var(--color-text)] cursor-pointer"
            @click="close"
            aria-label="Close help"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
        <p class="text-xs text-[var(--color-text-muted)] leading-relaxed">
          {{ entry.description }}
        </p>
        <a
          v-if="entry.learnMoreUrl"
          :href="entry.learnMoreUrl"
          target="_blank"
          rel="noopener noreferrer"
          class="inline-block mt-2 text-xs font-semibold text-[#2068FF] hover:underline"
        >
          Learn more &rarr;
        </a>
      </div>
    </Transition>

    <!-- Click-outside close -->
    <div v-if="isOpen" class="contextual-help-backdrop" @click="close" />
  </span>
</template>

<style scoped>
.contextual-help-wrapper {
  position: relative;
  display: inline-flex;
  align-items: center;
}

.contextual-help-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  color: var(--color-text-muted, #6b7280);
  opacity: 0.6;
  cursor: pointer;
  transition: opacity 0.15s, color 0.15s;
  border-radius: 50%;
}
.contextual-help-trigger:hover {
  opacity: 1;
  color: #2068FF;
}

.contextual-help-popover {
  position: absolute;
  z-index: 8000;
  width: 260px;
  padding: 12px;
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}
.contextual-help-popover--top {
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
}
.contextual-help-popover--bottom {
  top: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
}
.contextual-help-popover--left {
  right: calc(100% + 8px);
  top: 50%;
  transform: translateY(-50%);
}
.contextual-help-popover--right {
  left: calc(100% + 8px);
  top: 50%;
  transform: translateY(-50%);
}

.contextual-help-backdrop {
  position: fixed;
  inset: 0;
  z-index: 7999;
}

.help-pop-enter-active,
.help-pop-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.help-pop-enter-from,
.help-pop-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(4px);
}
</style>
