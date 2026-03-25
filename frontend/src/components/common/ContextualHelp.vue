<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { helpEntries } from '../../data/help-content'

const props = defineProps({
  entryId: {
    type: String,
    required: true,
    validator: (v) => v in helpEntries,
  },
  position: {
    type: String,
    default: 'top',
    validator: (v) => ['top', 'right', 'bottom', 'left'].includes(v),
  },
})

const isOpen = ref(false)
const trigger = ref(null)

const entry = computed(() => helpEntries[props.entryId])

function toggle(e) {
  e.stopPropagation()
  isOpen.value = !isOpen.value
}

function onClickOutside(e) {
  if (trigger.value && !trigger.value.contains(e.target)) {
    isOpen.value = false
  }
}

onMounted(() => document.addEventListener('click', onClickOutside))
onUnmounted(() => document.removeEventListener('click', onClickOutside))
</script>

<template>
  <span ref="trigger" class="contextual-help" :class="`contextual-help--${position}`">
    <button
      class="help-trigger"
      :class="{ 'help-trigger--active': isOpen }"
      @click="toggle"
      :aria-expanded="isOpen"
      :aria-label="`Help: ${entry?.title}`"
    >
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10" />
        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
      </svg>
    </button>

    <Transition name="help-pop">
      <div v-if="isOpen && entry" class="help-popover">
        <h4 class="text-sm font-bold text-[var(--color-text)] mb-1">{{ entry.title }}</h4>
        <p class="text-xs text-[var(--color-text-muted)] leading-relaxed">{{ entry.description }}</p>
        <a
          v-if="entry.learnMoreUrl"
          :href="entry.learnMoreUrl"
          target="_blank"
          rel="noopener"
          class="inline-block mt-2 text-xs font-semibold text-[#2068FF] hover:underline"
        >
          Learn more &rarr;
        </a>
      </div>
    </Transition>
  </span>
</template>

<style scoped>
.contextual-help {
  position: relative;
  display: inline-flex;
  align-items: center;
}

.help-trigger {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: color 0.15s, background-color 0.15s;
}
.help-trigger:hover,
.help-trigger--active {
  color: #2068FF;
  background: rgba(32, 104, 255, 0.08);
}

.help-popover {
  position: absolute;
  width: 260px;
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 10px;
  padding: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  z-index: 100;
}

/* Position variants */
.contextual-help--top .help-popover {
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
}
.contextual-help--bottom .help-popover {
  top: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
}
.contextual-help--left .help-popover {
  right: calc(100% + 8px);
  top: 50%;
  transform: translateY(-50%);
}
.contextual-help--right .help-popover {
  left: calc(100% + 8px);
  top: 50%;
  transform: translateY(-50%);
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
.contextual-help--bottom .help-pop-enter-from,
.contextual-help--bottom .help-pop-leave-to {
  transform: translateX(-50%) translateY(-4px);
}
.contextual-help--left .help-pop-enter-from,
.contextual-help--left .help-pop-leave-to {
  transform: translateY(-50%) translateX(4px);
}
.contextual-help--right .help-pop-enter-from,
.contextual-help--right .help-pop-leave-to {
  transform: translateY(-50%) translateX(-4px);
}
</style>
