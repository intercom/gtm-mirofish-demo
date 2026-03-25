<script setup>
import { useToast } from '../../composables/useToast'

const { toasts, removeToast } = useToast()

const icons = {
  success: '✓',
  error: '✕',
  info: 'ℹ',
}
</script>

<template>
  <Teleport to="body">
    <div class="fixed top-4 right-4 z-[9999] flex flex-col gap-2 pointer-events-none">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="toast-item pointer-events-auto flex items-start gap-2.5 px-4 py-3 rounded-lg shadow-lg text-sm font-medium min-w-[280px] max-w-[420px] relative overflow-hidden"
          :class="'toast--' + toast.type"
        >
          <span class="toast-icon">{{ icons[toast.type] }}</span>
          <span class="flex-1">{{ toast.message }}</span>
          <button
            @click="removeToast(toast.id)"
            class="toast-close shrink-0 text-base leading-none cursor-pointer"
          >
            &times;
          </button>
          <div
            v-if="toast.duration > 0"
            class="toast-progress"
            :style="{ animationDuration: toast.duration + 'ms' }"
          />
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
/* Type colors */
.toast--success { background: var(--color-success); color: white; }
.toast--error { background: var(--color-error); color: white; }
.toast--info { background: var(--color-primary); color: white; }

/* Icon pops in with a bouncy scale */
.toast-icon {
  font-size: 1rem;
  font-weight: 700;
  flex-shrink: 0;
  animation: icon-pop 350ms cubic-bezier(0.34, 1.56, 0.64, 1) 150ms both;
}

@keyframes icon-pop {
  from { opacity: 0; transform: scale(0); }
  to { opacity: 1; transform: scale(1); }
}

/* Close button */
.toast-close {
  opacity: 0.6;
  transition: opacity 150ms ease;
}
.toast-close:hover {
  opacity: 1;
}

/* Auto-dismiss progress bar shrinks left-to-right */
.toast-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: rgba(255, 255, 255, 0.3);
  transform-origin: left;
  animation: progress-shrink linear forwards;
}

@keyframes progress-shrink {
  from { transform: scaleX(1); }
  to { transform: scaleX(0); }
}

/* --- TransitionGroup: enter / leave / move --- */

/* Spring-like slide-in from right with overshoot */
.toast-enter-active {
  animation: toast-in 400ms cubic-bezier(0.22, 1, 0.36, 1);
}

/* Slide out to right */
.toast-leave-active {
  animation: toast-out 250ms ease-in forwards;
  position: absolute;
  width: 100%;
}

/* Smooth reflow when siblings shift */
.toast-move {
  transition: transform 300ms ease;
}

@keyframes toast-in {
  0% {
    transform: translateX(calc(100% + 1rem));
    opacity: 0;
  }
  60% {
    opacity: 1;
  }
  75% {
    transform: translateX(-6px);
  }
  100% {
    transform: translateX(0);
    opacity: 1;
  }
}

@keyframes toast-out {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(calc(100% + 1rem));
    opacity: 0;
  }
}
</style>
