<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { getHelpContent } from '../../data/help-content'

const props = defineProps({
  featureKey: {
    type: String,
    required: true,
  },
  size: {
    type: String,
    default: 'sm',
    validator: (v) => ['xs', 'sm'].includes(v),
  },
})

const open = ref(false)
const triggerRef = ref(null)
const popoverRef = ref(null)
const placement = ref('bottom')

const help = getHelpContent(props.featureKey)

function toggle() {
  if (open.value) {
    open.value = false
  } else {
    open.value = true
    nextTick(updatePlacement)
  }
}

function updatePlacement() {
  if (!triggerRef.value || !popoverRef.value) return
  const triggerRect = triggerRef.value.getBoundingClientRect()
  const popoverRect = popoverRef.value.getBoundingClientRect()
  const spaceBelow = window.innerHeight - triggerRect.bottom
  placement.value = spaceBelow < popoverRect.height + 12 ? 'top' : 'bottom'
}

function onClickOutside(e) {
  if (
    triggerRef.value?.contains(e.target) ||
    popoverRef.value?.contains(e.target)
  )
    return
  open.value = false
}

function onKeydown(e) {
  if (e.key === 'Escape') open.value = false
}

onMounted(() => {
  document.addEventListener('click', onClickOutside, true)
  document.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  document.removeEventListener('click', onClickOutside, true)
  document.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <span v-if="help" class="inline-flex items-center relative">
    <button
      ref="triggerRef"
      type="button"
      :class="[
        'inline-flex items-center justify-center rounded-full border transition-colors cursor-pointer',
        'text-[--color-text-muted] hover:text-[--color-primary] hover:border-[--color-primary]',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-[--color-primary] focus-visible:ring-offset-1',
        open ? 'bg-[--color-primary-light] text-[--color-primary] border-[--color-primary]' : 'border-[--color-border]',
        size === 'xs' ? 'w-4 h-4 text-[10px]' : 'w-5 h-5 text-xs',
      ]"
      :aria-label="`Help: ${help.title}`"
      :aria-expanded="open"
      @click.stop="toggle"
    >
      ?
    </button>

    <Transition name="help-pop">
      <div
        v-if="open"
        ref="popoverRef"
        :class="[
          'absolute z-50 w-72 rounded-lg border border-[--color-border] bg-[--color-surface] shadow-lg p-4',
          'left-1/2 -translate-x-1/2',
          placement === 'top' ? 'bottom-full mb-2' : 'top-full mt-2',
        ]"
        role="tooltip"
      >
        <div class="text-sm font-semibold text-[--color-text] mb-1">
          {{ help.title }}
        </div>
        <p class="text-xs leading-relaxed text-[--color-text-secondary] m-0">
          {{ help.description }}
        </p>
        <a
          v-if="help.learnMoreUrl"
          :href="help.learnMoreUrl"
          target="_blank"
          rel="noopener noreferrer"
          class="inline-flex items-center gap-1 text-xs font-medium text-[--color-primary] hover:underline mt-2"
        >
          Learn More
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </a>
      </div>
    </Transition>
  </span>
</template>

<style scoped>
.help-pop-enter-active,
.help-pop-leave-active {
  transition: opacity var(--transition-fast), transform var(--transition-fast);
}

.help-pop-enter-from,
.help-pop-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(4px);
}
</style>
