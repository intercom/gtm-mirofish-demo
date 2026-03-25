<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useNotificationStore } from '../../stores/notifications'

const store = useNotificationStore()
const isOpen = ref(false)
const containerRef = ref(null)

function toggle() {
  isOpen.value = !isOpen.value
}

function onClickOutside(e) {
  if (isOpen.value && containerRef.value && !containerRef.value.contains(e.target)) {
    isOpen.value = false
  }
}

function formatTime(ts) {
  const diff = Date.now() - ts
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'Just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

onMounted(() => document.addEventListener('click', onClickOutside))
onUnmounted(() => document.removeEventListener('click', onClickOutside))
</script>

<template>
  <div ref="containerRef" class="relative">
    <button
      @click="toggle"
      class="bell-button"
      aria-label="Notifications"
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
        <path d="M13.73 21a2 2 0 0 1-3.46 0" />
      </svg>
      <span
        v-if="store.unreadCount > 0"
        :key="store.unreadCount"
        class="badge"
      >
        {{ store.unreadCount > 9 ? '9+' : store.unreadCount }}
      </span>
    </button>

    <Transition name="panel">
      <div v-if="isOpen" class="panel">
        <div class="panel-header">
          <span class="panel-title">Notifications</span>
          <button
            v-if="store.unreadCount > 0"
            @click="store.markAllRead()"
            class="panel-action"
          >
            Mark all read
          </button>
        </div>

        <div v-if="store.notifications.length === 0" class="panel-empty">
          No notifications yet
        </div>

        <div v-else class="panel-list">
          <TransitionGroup name="notif-item">
            <div
              v-for="n in store.notifications"
              :key="n.id"
              class="notif-row"
              :class="{ 'notif-row--unread': !n.read }"
              @click="store.markRead(n.id)"
            >
              <span class="notif-dot" :class="'notif-dot--' + n.type" />
              <div class="notif-body">
                <div class="notif-title">{{ n.title }}</div>
                <div v-if="n.message" class="notif-message">{{ n.message }}</div>
                <div class="notif-time">{{ formatTime(n.timestamp) }}</div>
              </div>
              <button
                @click.stop="store.remove(n.id)"
                class="notif-dismiss"
              >
                &times;
              </button>
            </div>
          </TransitionGroup>
        </div>

        <div v-if="store.notifications.length > 0" class="panel-footer">
          <button @click="store.clear()" class="panel-action panel-action--muted">
            Clear all
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
/* ── Bell button ─────────────────────────────── */
.bell-button {
  position: relative;
  padding: 6px;
  color: rgba(255, 255, 255, 0.6);
  border-radius: var(--radius-sm);
  transition: color 150ms ease, background-color 150ms ease;
  cursor: pointer;
}
.bell-button:hover {
  color: white;
  background-color: rgba(255, 255, 255, 0.08);
}

/* ── Badge with pop animation ────────────────── */
.badge {
  position: absolute;
  top: 0;
  right: 0;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  font-size: 10px;
  font-weight: 700;
  line-height: 16px;
  text-align: center;
  color: white;
  background: var(--color-error);
  border-radius: 9999px;
  animation: badge-pop 350ms cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes badge-pop {
  0% { transform: scale(0); }
  60% { transform: scale(1.3); }
  100% { transform: scale(1); }
}

/* ── Dropdown panel ──────────────────────────── */
.panel {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 340px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  z-index: 50;
  transform-origin: top right;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
}

.panel-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--color-text);
}

.panel-action {
  font-size: 0.75rem;
  color: var(--color-primary);
  cursor: pointer;
  transition: opacity 150ms ease;
}
.panel-action:hover { opacity: 0.8; }

.panel-action--muted {
  color: var(--color-text-muted);
}
.panel-action--muted:hover {
  color: var(--color-text);
}

.panel-empty {
  padding: 32px 16px;
  text-align: center;
  font-size: 0.875rem;
  color: var(--color-text-muted);
}

.panel-list {
  max-height: 320px;
  overflow-y: auto;
  position: relative;
}

.panel-footer {
  padding: 10px 16px;
  border-top: 1px solid var(--color-border);
  text-align: center;
}

/* ── Panel open/close transitions ────────────── */
.panel-enter-active {
  animation: panel-in 250ms cubic-bezier(0.22, 1, 0.36, 1);
}
.panel-leave-active {
  animation: panel-out 200ms ease-in forwards;
}

@keyframes panel-in {
  from { opacity: 0; transform: scale(0.95) translateY(-4px); }
  to { opacity: 1; transform: scale(1) translateY(0); }
}
@keyframes panel-out {
  from { opacity: 1; transform: scale(1) translateY(0); }
  to { opacity: 0; transform: scale(0.95) translateY(-4px); }
}

/* ── Notification rows ───────────────────────── */
.notif-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 16px;
  cursor: pointer;
  transition: background-color 150ms ease;
}
.notif-row:hover { background: var(--color-tint); }
.notif-row--unread { background: var(--color-primary-lighter); }
.notif-row--unread:hover { background: var(--color-primary-light); }

.notif-dot {
  width: 8px;
  height: 8px;
  border-radius: 9999px;
  margin-top: 5px;
  flex-shrink: 0;
}
.notif-dot--info { background: var(--color-primary); }
.notif-dot--success { background: var(--color-success); }
.notif-dot--warning { background: var(--color-warning); }
.notif-dot--error { background: var(--color-error); }

.notif-body {
  flex: 1;
  min-width: 0;
}

.notif-title {
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.notif-message {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  margin-top: 2px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notif-time {
  font-size: 0.75rem;
  color: var(--color-text-muted);
  margin-top: 4px;
}

.notif-dismiss {
  flex-shrink: 0;
  font-size: 1rem;
  line-height: 1;
  color: var(--color-text-muted);
  opacity: 0;
  cursor: pointer;
  transition: opacity 150ms ease;
}
.notif-row:hover .notif-dismiss { opacity: 0.6; }
.notif-dismiss:hover { opacity: 1 !important; }

/* ── Notification list item transitions ──────── */
.notif-item-enter-active {
  transition: all 300ms cubic-bezier(0.22, 1, 0.36, 1);
}
.notif-item-leave-active {
  transition: all 200ms ease-in;
  position: absolute;
  width: 100%;
}
.notif-item-enter-from {
  opacity: 0;
  transform: translateX(-12px);
}
.notif-item-leave-to {
  opacity: 0;
  transform: translateX(12px);
}
.notif-item-move {
  transition: transform 300ms ease;
}
</style>
