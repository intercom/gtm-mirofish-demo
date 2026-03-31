<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  branchPoint: { type: Object, required: true },
  /** X position in pixels (relative to container) */
  x: { type: Number, required: true },
  /** Whether simulation is in replay/completed mode (enables "Branch Here") */
  replayMode: { type: Boolean, default: false },
})

const emit = defineEmits(['branch-here'])

const showTooltip = ref(false)
const expanded = ref(false)

const branchCount = computed(() => props.branchPoint.branches?.length || 0)

function toggle() {
  expanded.value = !expanded.value
}

function handleBranchHere() {
  emit('branch-here', props.branchPoint.round)
}
</script>

<template>
  <div
    class="branch-marker"
    :style="{ left: `${x}px` }"
  >
    <!-- Fork icon button -->
    <button
      class="fork-icon"
      @mouseenter="showTooltip = true"
      @mouseleave="showTooltip = false"
      @click.stop="toggle"
      :title="`Branch: ${branchPoint.label}`"
    >
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path d="M8 2v4M8 6L4 10M8 6l4 4M4 10v2M12 10v2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        <circle cx="8" cy="2" r="1.5" fill="currentColor"/>
        <circle cx="4" cy="12" r="1.5" fill="currentColor"/>
        <circle cx="12" cy="12" r="1.5" fill="currentColor"/>
      </svg>
      <span class="fork-badge">{{ branchCount }}</span>
    </button>

    <!-- Tooltip (hover) -->
    <Transition name="tooltip-fade">
      <div v-if="showTooltip && !expanded" class="branch-tooltip">
        <div class="tooltip-label">{{ branchPoint.label }}</div>
        <div class="tooltip-meta">Round {{ branchPoint.round }} · {{ branchCount }} branches</div>
        <div class="tooltip-branches">
          <div v-for="b in branchPoint.branches" :key="b.id" class="tooltip-branch-row">
            <span class="tooltip-branch-dot" />
            <span>{{ b.label }}</span>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Expanded mini tree (click) -->
    <Transition name="tree-expand">
      <div v-if="expanded" class="branch-tree-mini" @click.stop>
        <div class="tree-header">
          <span class="tree-title">{{ branchPoint.label }}</span>
          <button class="tree-close" @click="expanded = false">&times;</button>
        </div>
        <div class="tree-content">
          <div
            v-for="(branch, idx) in branchPoint.branches"
            :key="branch.id"
            class="tree-branch"
          >
            <div class="tree-branch-connector">
              <div class="connector-line" />
              <div class="connector-dot" />
            </div>
            <div class="tree-branch-info">
              <div class="tree-branch-label">{{ branch.label }}</div>
              <div class="tree-branch-outcome">{{ branch.outcome }}</div>
            </div>
          </div>
        </div>
        <button
          v-if="replayMode"
          class="branch-here-btn"
          @click="handleBranchHere"
        >
          <svg width="12" height="12" viewBox="0 0 16 16" fill="none">
            <path d="M8 2v4M8 6L4 10M8 6l4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Branch Here
        </button>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.branch-marker {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  z-index: 10;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.fork-icon {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(32, 104, 255, 0.1);
  color: var(--color-primary, #2068FF);
  border: 1.5px solid rgba(32, 104, 255, 0.3);
  cursor: pointer;
  transition: all 0.15s ease;
}

.fork-icon:hover {
  background: rgba(32, 104, 255, 0.18);
  border-color: var(--color-primary, #2068FF);
  transform: scale(1.1);
}

.fork-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 14px;
  height: 14px;
  padding: 0 3px;
  border-radius: 7px;
  background: var(--color-primary, #2068FF);
  color: white;
  font-size: 9px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

/* Tooltip */
.branch-tooltip {
  position: absolute;
  top: 34px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #e5e5e5);
  border-radius: 8px;
  padding: 10px 12px;
  min-width: 180px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
  pointer-events: none;
}

.tooltip-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text, #1a1a1a);
  margin-bottom: 2px;
}

.tooltip-meta {
  font-size: 10px;
  color: var(--color-text-muted, #888);
  margin-bottom: 6px;
}

.tooltip-branches {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.tooltip-branch-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: var(--color-text-secondary, #555);
}

.tooltip-branch-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--color-primary, #2068FF);
  flex-shrink: 0;
}

/* Expanded tree */
.branch-tree-mini {
  position: absolute;
  top: 34px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #e5e5e5);
  border-radius: 10px;
  padding: 12px;
  min-width: 240px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.14);
  z-index: 20;
}

.tree-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.tree-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text, #1a1a1a);
}

.tree-close {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  color: var(--color-text-muted, #888);
  padding: 0 2px;
}
.tree-close:hover {
  color: var(--color-text, #1a1a1a);
}

.tree-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tree-branch {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.tree-branch-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 4px;
  flex-shrink: 0;
  width: 12px;
}

.connector-line {
  width: 1.5px;
  height: 12px;
  background: rgba(32, 104, 255, 0.3);
}

.connector-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary, #2068FF);
  border: 1.5px solid var(--color-surface, #fff);
  box-shadow: 0 0 0 1px rgba(32, 104, 255, 0.3);
}

.tree-branch-info {
  flex: 1;
  min-width: 0;
}

.tree-branch-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text, #1a1a1a);
}

.tree-branch-outcome {
  font-size: 10px;
  color: var(--color-text-muted, #888);
  margin-top: 1px;
}

/* Branch Here button */
.branch-here-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  width: 100%;
  margin-top: 10px;
  padding: 6px 0;
  border-radius: 6px;
  border: 1px dashed rgba(32, 104, 255, 0.4);
  background: rgba(32, 104, 255, 0.04);
  color: var(--color-primary, #2068FF);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}
.branch-here-btn:hover {
  background: rgba(32, 104, 255, 0.1);
  border-color: var(--color-primary, #2068FF);
}

/* Transitions */
.tooltip-fade-enter-active { transition: opacity 0.15s ease, transform 0.15s ease; }
.tooltip-fade-leave-active { transition: opacity 0.1s ease; }
.tooltip-fade-enter-from { opacity: 0; transform: translateX(-50%) translateY(-4px); }
.tooltip-fade-leave-to { opacity: 0; }

.tree-expand-enter-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.tree-expand-leave-active { transition: opacity 0.15s ease, transform 0.15s ease; }
.tree-expand-enter-from { opacity: 0; transform: translateX(-50%) translateY(-6px) scale(0.95); }
.tree-expand-leave-to { opacity: 0; transform: translateX(-50%) scale(0.95); }
</style>
