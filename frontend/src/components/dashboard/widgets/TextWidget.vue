<script setup>
import { ref, computed } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  config: {
    type: Object,
    default: () => ({}),
  },
  data: {
    type: [String, Object],
    default: '',
  },
  loading: Boolean,
  error: String,
  onConfigChange: Function,
})

const editing = ref(false)
const editContent = ref('')

const content = computed(() => props.config.content || (typeof props.data === 'string' ? props.data : '') || '')

const fontSize = computed(() => props.config.fontSize || 'base')

const alignment = computed(() => props.config.alignment || 'left')

const fontSizeClass = computed(() => {
  const map = {
    xs: 'text-xs',
    sm: 'text-sm',
    base: 'text-base',
    lg: 'text-lg',
    xl: 'text-xl',
    '2xl': 'text-2xl',
  }
  return map[fontSize.value] || 'text-base'
})

const alignClass = computed(() => {
  const map = { left: 'text-left', center: 'text-center', right: 'text-right' }
  return map[alignment.value] || 'text-left'
})

const renderedHtml = computed(() => {
  if (!content.value) return ''
  return marked.parse(content.value, { breaks: true, gfm: true })
})

function startEditing() {
  editContent.value = content.value
  editing.value = true
}

function saveEdit() {
  if (props.onConfigChange) {
    props.onConfigChange({ ...props.config, content: editContent.value })
  }
  editing.value = false
}

function cancelEdit() {
  editing.value = false
}

function emitConfig(patch) {
  if (props.onConfigChange) {
    props.onConfigChange({ ...props.config, ...patch })
  }
}
</script>

<template>
  <div class="text-widget" :class="alignClass">
    <!-- Error state -->
    <div v-if="error" class="flex items-center justify-center h-full min-h-[80px] text-[var(--color-error)] text-sm">
      {{ error }}
    </div>

    <!-- Loading state -->
    <div v-else-if="loading" class="flex flex-col gap-2 p-2">
      <div class="skeleton-line w-3/4" />
      <div class="skeleton-line w-full" />
      <div class="skeleton-line w-1/2" />
    </div>

    <!-- Edit mode -->
    <div v-else-if="editing" class="text-widget-editor">
      <div class="editor-toolbar">
        <div class="flex items-center gap-2">
          <select :value="fontSize" class="toolbar-select" @change="emitConfig({ fontSize: $event.target.value })">
            <option value="xs">Extra Small</option>
            <option value="sm">Small</option>
            <option value="base">Normal</option>
            <option value="lg">Large</option>
            <option value="xl">X-Large</option>
            <option value="2xl">2X-Large</option>
          </select>
          <div class="align-group">
            <button
              v-for="align in ['left', 'center', 'right']"
              :key="align"
              :class="['align-btn', alignment === align && 'active']"
              @click="emitConfig({ alignment: align })"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <template v-if="align === 'left'">
                  <path stroke-linecap="round" stroke-width="2" d="M3 6h18M3 12h12M3 18h16" />
                </template>
                <template v-else-if="align === 'center'">
                  <path stroke-linecap="round" stroke-width="2" d="M3 6h18M6 12h12M4 18h16" />
                </template>
                <template v-else>
                  <path stroke-linecap="round" stroke-width="2" d="M3 6h18M9 12h12M6 18h16" />
                </template>
              </svg>
            </button>
          </div>
        </div>
        <div class="flex gap-2">
          <button class="toolbar-btn cancel" @click="cancelEdit">Cancel</button>
          <button class="toolbar-btn save" @click="saveEdit">Save</button>
        </div>
      </div>
      <textarea
        v-model="editContent"
        class="editor-textarea"
        placeholder="Write markdown content..."
        rows="6"
      />
      <span class="text-[10px] text-[var(--color-text-muted)] mt-1">Supports Markdown: **bold**, *italic*, # headings, - lists, [links](url)</span>
    </div>

    <!-- Rendered content -->
    <template v-else>
      <div
        v-if="renderedHtml"
        class="text-widget-content"
        :class="[fontSizeClass, alignClass]"
        v-html="renderedHtml"
      />
      <div v-else class="flex flex-col items-center justify-center h-full min-h-[80px] text-[var(--color-text-muted)] text-sm gap-1">
        <span>No content</span>
      </div>
      <div v-if="onConfigChange" class="text-widget-footer" :class="alignClass">
        <button class="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-primary)]" @click="startEditing">
          Edit text
        </button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.text-widget {
  display: flex;
  flex-direction: column;
  height: 100%;
  font-family: var(--font-family);
}

.text-widget-content {
  flex: 1;
  color: var(--color-text);
  line-height: var(--leading-normal);
  overflow: auto;
}

.text-widget-content :deep(h1) {
  font-size: var(--text-2xl);
  font-weight: var(--font-bold);
  margin-bottom: 0.5em;
  letter-spacing: var(--letter-spacing-tight);
}

.text-widget-content :deep(h2) {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  margin-bottom: 0.4em;
}

.text-widget-content :deep(h3) {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  margin-bottom: 0.3em;
}

.text-widget-content :deep(p) {
  margin-bottom: 0.6em;
}

.text-widget-content :deep(p:last-child) {
  margin-bottom: 0;
}

.text-widget-content :deep(strong) {
  font-weight: var(--font-semibold);
}

.text-widget-content :deep(a) {
  color: var(--color-primary);
  text-decoration: none;
}

.text-widget-content :deep(a:hover) {
  text-decoration: underline;
}

.text-widget-content :deep(ul),
.text-widget-content :deep(ol) {
  padding-left: 1.5em;
  margin-bottom: 0.6em;
}

.text-widget-content :deep(li) {
  margin-bottom: 0.2em;
}

.text-widget-content :deep(code) {
  font-family: var(--font-mono);
  font-size: 0.9em;
  background: var(--color-tint);
  padding: 0.1em 0.3em;
  border-radius: var(--radius-sm);
}

.text-widget-content :deep(pre) {
  background: var(--color-tint);
  padding: var(--space-3);
  border-radius: var(--radius);
  overflow-x: auto;
  margin-bottom: 0.6em;
}

.text-widget-content :deep(pre code) {
  background: none;
  padding: 0;
}

.text-widget-content :deep(blockquote) {
  border-left: 3px solid var(--color-primary);
  padding-left: var(--space-3);
  color: var(--color-text-secondary);
  margin-bottom: 0.6em;
}

.text-widget-content :deep(hr) {
  border: none;
  border-top: 1px solid var(--color-border);
  margin: 0.8em 0;
}

.text-widget-footer {
  padding-top: var(--space-2);
}

.text-widget-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-2);
  flex-wrap: wrap;
  gap: var(--space-2);
}

.toolbar-select {
  padding: var(--space-1) var(--space-2);
  font-size: var(--text-xs);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  color: var(--color-text);
  outline: none;
}

.toolbar-select:focus {
  border-color: var(--color-primary);
}

.align-group {
  display: flex;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.align-btn {
  padding: var(--space-1) var(--space-2);
  background: var(--color-surface);
  color: var(--color-text-muted);
  border: none;
  cursor: pointer;
  transition: var(--transition-fast);
}

.align-btn:not(:last-child) {
  border-right: 1px solid var(--color-border);
}

.align-btn.active {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.align-btn:hover:not(.active) {
  background: var(--color-tint);
}

.toolbar-btn {
  padding: var(--space-1) var(--space-3);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: var(--transition-fast);
}

.toolbar-btn.cancel {
  background: var(--color-surface);
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
}

.toolbar-btn.cancel:hover {
  color: var(--color-text);
}

.toolbar-btn.save {
  background: var(--color-primary);
  color: white;
  border: none;
}

.toolbar-btn.save:hover {
  background: var(--color-primary-hover);
}

.editor-textarea {
  flex: 1;
  width: 100%;
  padding: var(--space-3);
  font-size: var(--text-sm);
  font-family: var(--font-mono);
  line-height: var(--leading-relaxed);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface);
  color: var(--color-text);
  resize: vertical;
  outline: none;
}

.editor-textarea:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px var(--input-ring);
}

.skeleton-line {
  height: 12px;
  border-radius: var(--radius-sm);
  background: var(--color-border);
  animation: shimmer 1.5s ease-in-out infinite alternate;
}

@keyframes shimmer {
  from { opacity: 0.4; }
  to { opacity: 0.7; }
}
</style>
