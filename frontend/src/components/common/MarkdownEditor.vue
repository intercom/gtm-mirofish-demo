<script setup>
import { ref, computed } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  rows: { type: [Number, String], default: 16 },
  filename: { type: String, default: 'document' },
})

const emit = defineEmits(['update:modelValue'])

const showPreview = ref(false)
const fileInput = ref(null)

const renderedHtml = computed(() => marked.parse(props.modelValue || ''))

function onInput(e) {
  emit('update:modelValue', e.target.value)
}

function importFile() {
  fileInput.value?.click()
}

function handleFileSelect(e) {
  const file = e.target.files?.[0]
  if (!file) return

  const reader = new FileReader()
  reader.onload = (ev) => {
    emit('update:modelValue', ev.target.result)
    if (showPreview.value) showPreview.value = false
  }
  reader.readAsText(file)

  // Reset so the same file can be re-imported
  e.target.value = ''
}

function exportFile() {
  const content = props.modelValue || ''
  const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${props.filename}.md`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div>
    <!-- Toolbar -->
    <div class="flex items-center justify-between mb-2">
      <div class="flex items-center gap-2">
        <button
          type="button"
          @click="importFile"
          class="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded-md border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-tint)] hover:text-[var(--color-text)] transition-colors"
          title="Import Markdown file"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
          </svg>
          Import .md
        </button>
        <button
          type="button"
          @click="exportFile"
          :disabled="!modelValue"
          class="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded-md border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-tint)] hover:text-[var(--color-text)] transition-colors disabled:opacity-40 disabled:pointer-events-none"
          title="Export as Markdown file"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Export .md
        </button>
      </div>
      <button
        type="button"
        @click="showPreview = !showPreview"
        class="inline-flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded-md transition-colors"
        :class="showPreview
          ? 'bg-[#2068FF] text-white'
          : 'border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-tint)] hover:text-[var(--color-text)]'"
      >
        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
        </svg>
        Preview
      </button>
    </div>

    <!-- Hidden file input -->
    <input
      ref="fileInput"
      type="file"
      accept=".md,.markdown,.txt,.text"
      class="hidden"
      @change="handleFileSelect"
    />

    <!-- Editor / Preview -->
    <div v-if="showPreview" class="md-preview w-full border border-[var(--color-border)] rounded-lg p-3 md:p-4 bg-[var(--color-surface)] overflow-y-auto" :style="{ minHeight: `${(Number(rows) * 1.5) + 2}rem` }">
      <div v-if="modelValue" v-html="renderedHtml" />
      <p v-else class="text-sm text-[var(--color-text-muted)] italic">Nothing to preview</p>
    </div>
    <textarea
      v-else
      :value="modelValue"
      @input="onInput"
      :rows="rows"
      :placeholder="placeholder"
      class="w-full border border-[var(--color-border)] rounded-lg p-3 md:p-4 text-sm leading-relaxed focus:ring-2 focus:ring-[var(--color-primary)] focus:border-transparent resize-y bg-[var(--color-surface)]"
    />
  </div>
</template>

<style scoped>
.md-preview :deep(h1) { font-size: 1.5rem; font-weight: 600; margin-bottom: 0.75rem; color: var(--color-text); }
.md-preview :deep(h2) { font-size: 1.25rem; font-weight: 600; margin-top: 1.5rem; margin-bottom: 0.5rem; color: var(--color-text); }
.md-preview :deep(h3) { font-size: 1.125rem; font-weight: 600; margin-top: 1rem; margin-bottom: 0.5rem; color: var(--color-text); }
.md-preview :deep(p) { margin-bottom: 0.75rem; line-height: 1.625; color: var(--color-text-secondary); font-size: 0.875rem; }
.md-preview :deep(ul),
.md-preview :deep(ol) { margin-bottom: 0.75rem; padding-left: 1.5rem; }
.md-preview :deep(li) { margin-bottom: 0.25rem; line-height: 1.625; color: var(--color-text-secondary); font-size: 0.875rem; }
.md-preview :deep(ul) { list-style-type: disc; }
.md-preview :deep(ol) { list-style-type: decimal; }
.md-preview :deep(strong) { font-weight: 600; color: var(--color-text); }
.md-preview :deep(blockquote) {
  border-left: 3px solid var(--color-primary);
  padding-left: 1rem;
  margin: 1rem 0;
  color: var(--color-text-secondary);
  font-style: italic;
}
.md-preview :deep(code) {
  background: var(--color-tint);
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.8125rem;
}
.md-preview :deep(pre) {
  background: #1a1a2e;
  color: #e0e0e0;
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin: 1rem 0;
}
.md-preview :deep(pre code) { background: none; padding: 0; }
</style>
