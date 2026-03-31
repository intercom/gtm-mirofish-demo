<script setup>
import { useToast } from '../../composables/useToast'

const { toasts, removeToast } = useToast()

function handleAction(toast) {
  if (toast.action?.onClick) {
    toast.action.onClick()
  }
  removeToast(toast.id)
}
</script>

<template>
  <Teleport to="body">
    <div
      aria-live="polite"
      aria-relevant="additions removals"
      class="fixed top-4 right-4 left-4 sm:left-auto z-[9999] flex flex-col gap-2.5 pointer-events-none"
    >
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          :role="toast.type === 'error' ? 'alert' : 'status'"
          class="toast pointer-events-auto flex flex-col rounded-lg shadow-lg overflow-hidden min-w-0 w-[min(420px,calc(100vw-2rem))] relative"
          :class="[`toast--${toast.type}`]"
        >
          <div class="flex items-center gap-2.5 px-4 py-3">
            <!-- Icon -->
            <span class="toast__icon shrink-0" aria-hidden="true">
              <svg v-if="toast.type === 'success'" width="18" height="18" viewBox="0 0 18 18" fill="none">
                <circle cx="9" cy="9" r="9" fill="currentColor" opacity="0.2" />
                <path d="M5.5 9.5L7.5 11.5L12.5 6.5" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" />
              </svg>
              <svg v-else-if="toast.type === 'error'" width="18" height="18" viewBox="0 0 18 18" fill="none">
                <circle cx="9" cy="9" r="9" fill="currentColor" opacity="0.2" />
                <path d="M6.5 6.5L11.5 11.5M11.5 6.5L6.5 11.5" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" />
              </svg>
              <svg v-else-if="toast.type === 'warning'" width="18" height="18" viewBox="0 0 18 18" fill="none">
                <path d="M9 2L16.5 15.5H1.5L9 2Z" fill="currentColor" opacity="0.2" />
                <path d="M9 7V10.5" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" />
                <circle cx="9" cy="13" r="0.75" fill="currentColor" />
              </svg>
              <svg v-else width="18" height="18" viewBox="0 0 18 18" fill="none">
                <circle cx="9" cy="9" r="9" fill="currentColor" opacity="0.2" />
                <path d="M9 8V12.5" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" />
                <circle cx="9" cy="5.75" r="0.75" fill="currentColor" />
              </svg>
            </span>

            <!-- Message -->
            <span class="flex-1 text-sm font-medium leading-snug">{{ toast.message }}</span>

            <!-- Action button -->
            <button
              v-if="toast.action"
              @click="handleAction(toast)"
              class="toast__action shrink-0 text-xs font-semibold px-2 py-0.5 rounded cursor-pointer"
            >
              {{ toast.action.label }}
            </button>

            <!-- Close button -->
            <button
              @click="removeToast(toast.id)"
              class="toast-close shrink-0 text-base leading-none cursor-pointer"
              aria-label="Dismiss notification"
            >
              &times;
            </button>
          </div>

          <!-- Progress bar -->
          <div
            v-if="toast.duration > 0"
            class="toast__progress"
            :style="{ animationDuration: toast.duration + 'ms' }"
          />
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
/* ── Type variants using brand tokens ────────────────────────── */
.toast--success { background: var(--color-success); color: #fff; }
.toast--error { background: var(--color-error); color: #fff; }
.toast--warning { background: var(--color-warning); color: #1a1a1a; }
.toast--info { background: var(--color-primary); color: #fff; }

/* ── Action button per-type ──────────────────────────────────── */
.toast--success .toast__action { background: rgba(255, 255, 255, 0.2); color: #fff; }
.toast--success .toast__action:hover { background: rgba(255, 255, 255, 0.35); }
.toast--error .toast__action { background: rgba(255, 255, 255, 0.2); color: #fff; }
.toast--error .toast__action:hover { background: rgba(255, 255, 255, 0.35); }
.toast--warning .toast__action { background: rgba(0, 0, 0, 0.1); color: #1a1a1a; }
.toast--warning .toast__action:hover { background: rgba(0, 0, 0, 0.2); }
.toast--info .toast__action { background: rgba(255, 255, 255, 0.2); color: #fff; }
.toast--info .toast__action:hover { background: rgba(255, 255, 255, 0.35); }

/* ── Icon pop-in animation ───────────────────────────────────── */
.toast__icon {
  animation: icon-pop 350ms cubic-bezier(0.34, 1.56, 0.64, 1) 150ms both;
}

@keyframes icon-pop {
  from { opacity: 0; transform: scale(0); }
  to { opacity: 1; transform: scale(1); }
}

/* ── Close button ────────────────────────────────────────────── */
.toast-close {
  opacity: 0.6;
  transition: opacity 150ms ease;
}
.toast-close:hover {
  opacity: 1;
}

/* ── Progress bar ────────────────────────────────────────────── */
.toast__progress {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: rgba(255, 255, 255, 0.3);
  transform-origin: left;
  animation: progress-shrink linear forwards;
}
.toast--warning .toast__progress {
  background: rgba(0, 0, 0, 0.15);
}

@keyframes progress-shrink {
  from { transform: scaleX(1); }
  to { transform: scaleX(0); }
}

/* ── TransitionGroup: enter / leave / move ───────────────────── */
.toast-enter-active {
  animation: toast-in 400ms cubic-bezier(0.22, 1, 0.36, 1);
}

.toast-leave-active {
  animation: toast-out 250ms ease-in forwards;
  position: absolute;
  width: 100%;
}

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
