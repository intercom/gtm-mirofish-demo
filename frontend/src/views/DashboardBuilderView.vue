<script setup>
import { ref, onMounted } from 'vue'
import { useDashboardStore } from '../stores/dashboards.js'
import DashboardGrid from '../components/dashboard/DashboardGrid.vue'
import WidgetPicker from '../components/dashboard/WidgetPicker.vue'
import Button from '../components/common/Button.vue'

const store = useDashboardStore()

const editing = ref(true)
const pickerOpen = ref(false)

onMounted(() => {
  if (!store.activeDashboard) {
    store.createDashboard()
  }
})

function onAddWidget(payload) {
  if (!store.activeDashboard) return
  const layout = store.activeDashboard.layout
  const maxY = layout.reduce((max, item) => Math.max(max, item.y + item.h), 0)
  const newItem = {
    i: `widget-${Date.now()}`,
    x: 0,
    y: maxY,
    w: payload.size.w,
    h: payload.size.h,
    type: payload.type,
    config: { ...payload.config },
  }
  store.updateLayout(store.activeDashboardId, [...layout, newItem])
}

function onUpdateLayout(newLayout) {
  if (store.activeDashboard) {
    store.updateLayout(store.activeDashboardId, newLayout)
  }
}

function onRemoveWidget(widgetId) {
  if (store.activeDashboard) {
    store.removeWidget(store.activeDashboardId, widgetId)
  }
}

function onNameInput(e) {
  if (store.activeDashboard) {
    store.renameDashboard(store.activeDashboardId, e.target.value)
  }
}
</script>

<template>
  <div class="builder-view">
    <!-- Toolbar -->
    <header class="builder-toolbar">
      <div class="toolbar-left">
        <input
          v-if="store.activeDashboard"
          :value="store.activeDashboard.name"
          @input="onNameInput"
          class="dashboard-name-input"
          placeholder="Dashboard name"
        />
      </div>
      <div class="toolbar-right">
        <Button
          v-if="editing"
          variant="primary"
          size="sm"
          @click="pickerOpen = true"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right: 4px;">
            <path d="M12 5v14M5 12h14" />
          </svg>
          Add Widget
        </Button>
        <Button
          :variant="editing ? 'secondary' : 'ghost'"
          size="sm"
          @click="editing = !editing"
        >
          {{ editing ? 'Done' : 'Edit' }}
        </Button>
      </div>
    </header>

    <!-- Grid -->
    <main class="builder-canvas">
      <DashboardGrid
        v-if="store.activeDashboard"
        :layout="store.activeDashboard.layout"
        :editing="editing"
        @update:layout="onUpdateLayout"
        @remove-widget="onRemoveWidget"
      />
    </main>

    <!-- Widget Picker slide-over -->
    <WidgetPicker
      :open="pickerOpen"
      @close="pickerOpen = false"
      @add-widget="onAddWidget"
    />
  </div>
</template>

<style scoped>
.builder-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
}

.builder-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-5);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface);
  flex-shrink: 0;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.dashboard-name-input {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text);
  background: transparent;
  border: 1px solid transparent;
  border-radius: var(--radius);
  padding: var(--space-1) var(--space-2);
  outline: none;
  transition: var(--transition-fast);
  min-width: 200px;
}

.dashboard-name-input:hover {
  border-color: var(--color-border);
}

.dashboard-name-input:focus {
  border-color: var(--color-primary);
  background: var(--color-surface);
}

.builder-canvas {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-5);
}
</style>
