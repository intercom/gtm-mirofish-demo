<script setup>
import { ref, watch } from 'vue'
import { marked } from 'marked'
import EditorPopover from './EditorPopover.vue'

const props = defineProps({
  open: Boolean,
  section: {
    type: Object,
    default: () => ({ content: '' }),
  },
})

const emit = defineEmits(['update', 'done', 'cancel'])

const content = ref('')
const textareaRef = ref(null)
let snapshot = ''

watch(() => props.open, (isOpen) => {
  if (isOpen) {
    content.value = props.section.content || ''
    snapshot = content.value
  }
})

function onInput() {
  emit('update', { ...props.section, content: content.value })
}

function wrapSelection(before, after) {
  const el = textareaRef.value
  if (!el) return
  const start = el.selectionStart
  const end = el.selectionEnd
  const text = content.value
  const selected = text.slice(start, end)
  const replacement = `${before}${selected || 'text'}${after}`
  content.value = text.slice(0, start) + replacement + text.slice(end)
  onInput()
  requestAnimationFrame(() => {
    const newCursorStart = start + before.length
    const newCursorEnd = newCursorStart + (selected || 'text').length
    el.focus()
    el.setSelectionRange(newCursorStart, newCursorEnd)
  })
}

function insertAtLineStart(prefix) {
  const el = textareaRef.value
  if (!el) return
  const start = el.selectionStart
  const text = content.value
  const lineStart = text.lastIndexOf('\n', start - 1) + 1
  content.value = text.slice(0, lineStart) + prefix + text.slice(lineStart)
  onInput()
  requestAnimationFrame(() => {
    el.focus()
    el.setSelectionRange(start + prefix.length, start + prefix.length)
  })
}

function onDone() {
  emit('done')
}

function onCancel() {
  content.value = snapshot
  emit('update', { ...props.section, content: snapshot })
  emit('cancel')
}

const toolbarActions = [
  { label: 'B', title: 'Bold', action: () => wrapSelection('**', '**'), style: 'font-weight: 700' },
  { label: 'I', title: 'Italic', action: () => wrapSelection('*', '*'), style: 'font-style: italic' },
  { label: 'H2', title: 'Heading 2', action: () => insertAtLineStart('## ') },
  { label: 'H3', title: 'Heading 3', action: () => insertAtLineStart('### ') },
  { label: '•', title: 'Bullet list', action: () => insertAtLineStart('- ') },
]
</script>

<template>
  <EditorPopover :open="open" title="Edit Text Section" @done="onDone" @cancel="onCancel">
    <!-- Toolbar -->
    <div class="flex items-center gap-1 mb-3 pb-3 border-b border-[var(--color-border)]">
      <button
        v-for="btn in toolbarActions"
        :key="btn.label"
        :title="btn.title"
        :style="btn.style"
        class="w-8 h-8 rounded-md text-xs flex items-center justify-center text-[var(--color-text-secondary)] hover:bg-[var(--color-tint)] hover:text-[var(--color-text)] transition-colors cursor-pointer"
        @click="btn.action"
      >
        {{ btn.label }}
      </button>
    </div>

    <!-- Markdown textarea -->
    <textarea
      ref="textareaRef"
      v-model="content"
      @input="onInput"
      rows="12"
      placeholder="Write markdown content..."
      class="w-full bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2.5 text-sm text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[#2068FF] focus:ring-1 focus:ring-[#2068FF] transition-colors resize-y font-mono leading-relaxed"
    />

    <!-- Live preview -->
    <div class="mt-4">
      <p class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Preview</p>
      <div
        class="report-preview border border-[var(--color-border)] rounded-lg p-4 text-sm bg-[var(--color-tint)] min-h-[60px]"
        v-html="marked.parse(content || '*No content*')"
      />
    </div>
  </EditorPopover>
</template>

<style scoped>
.report-preview :deep(h2) { font-size: 1.125rem; font-weight: 600; margin-bottom: 0.5rem; color: var(--color-text); }
.report-preview :deep(h3) { font-size: 1rem; font-weight: 600; margin-bottom: 0.375rem; color: var(--color-text); }
.report-preview :deep(p) { margin-bottom: 0.5rem; line-height: 1.6; color: var(--color-text-secondary); }
.report-preview :deep(ul) { list-style-type: disc; padding-left: 1.25rem; margin-bottom: 0.5rem; }
.report-preview :deep(li) { margin-bottom: 0.125rem; line-height: 1.6; color: var(--color-text-secondary); }
.report-preview :deep(strong) { font-weight: 600; color: var(--color-text); }
.report-preview :deep(em) { font-style: italic; }
</style>
