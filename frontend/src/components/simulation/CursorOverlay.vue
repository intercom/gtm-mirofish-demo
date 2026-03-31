<script setup>
import { computed } from 'vue'
import { usePresenceStore } from '../../stores/presence'

const store = usePresenceStore()

const visibleCursors = computed(() =>
  store.cursors.filter(c => !c.is_typing || Math.random() > 0.1),
)
</script>

<template>
  <div class="cursor-overlay">
    <TransitionGroup
      enter-active-class="transition-all duration-300 ease-out"
      enter-from-class="opacity-0 scale-75"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition-all duration-200 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-75"
    >
      <div
        v-for="cursor in visibleCursors"
        :key="cursor.user_id"
        class="cursor-pointer-wrap"
        :style="{
          left: `${cursor.x * 100}%`,
          top: `${cursor.y * 100}%`,
        }"
      >
        <!-- Cursor arrow -->
        <svg
          class="cursor-arrow"
          width="16"
          height="20"
          viewBox="0 0 16 20"
          fill="none"
        >
          <path
            d="M1 1L6.5 18L9 10.5L15 8.5L1 1Z"
            :fill="cursor.color"
            stroke="white"
            stroke-width="1"
            stroke-linejoin="round"
          />
        </svg>

        <!-- Name label -->
        <div
          class="cursor-label"
          :style="{ backgroundColor: cursor.color }"
        >
          {{ cursor.name.split(' ')[0] }}
          <span v-if="cursor.is_typing" class="typing-dots">
            <span /><span /><span />
          </span>
        </div>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
.cursor-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
  z-index: 30;
}

.cursor-pointer-wrap {
  position: absolute;
  transition: left 800ms cubic-bezier(0.16, 1, 0.3, 1),
              top 800ms cubic-bezier(0.16, 1, 0.3, 1);
  will-change: left, top;
}

.cursor-arrow {
  filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3));
}

.cursor-label {
  position: absolute;
  top: 14px;
  left: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 600;
  color: white;
  white-space: nowrap;
  line-height: 1.4;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
}

.typing-dots {
  display: inline-flex;
  gap: 2px;
  margin-left: 3px;
  vertical-align: middle;
}

.typing-dots span {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.8);
  animation: typing-bounce 1.2s ease-in-out infinite;
}

.typing-dots span:nth-child(2) { animation-delay: 0.15s; }
.typing-dots span:nth-child(3) { animation-delay: 0.3s; }

@keyframes typing-bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-3px); }
}
</style>
