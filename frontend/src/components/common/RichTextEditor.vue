<script setup>
import { watch, onBeforeUnmount, computed } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Link from '@tiptap/extension-link'
import Placeholder from '@tiptap/extension-placeholder'
import CharacterCount from '@tiptap/extension-character-count'
import EditorToolbar from './EditorToolbar.vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: 'Start typing...' },
  charLimit: { type: Number, default: 0 },
  editable: { type: Boolean, default: true },
})

const emit = defineEmits(['update:modelValue'])

const extensions = [
  StarterKit.configure({
    heading: { levels: [2, 3] },
  }),
  Link.configure({
    openOnClick: false,
    HTMLAttributes: { class: 'editor-link' },
  }),
  Placeholder.configure({ placeholder: props.placeholder }),
  ...(props.charLimit > 0
    ? [CharacterCount.configure({ limit: props.charLimit })]
    : []),
]

const editor = useEditor({
  content: props.modelValue,
  extensions,
  editable: props.editable,
  onUpdate: ({ editor: e }) => {
    emit('update:modelValue', e.getHTML())
  },
})

const charCount = computed(() => {
  if (!editor.value) return 0
  return editor.value.storage.characterCount?.characters() ?? 0
})

const isOverLimit = computed(() => props.charLimit > 0 && charCount.value > props.charLimit)

watch(() => props.modelValue, (val) => {
  if (!editor.value) return
  const current = editor.value.getHTML()
  if (val !== current) {
    editor.value.commands.setContent(val, false)
  }
})

watch(() => props.editable, (val) => {
  editor.value?.setEditable(val)
})

onBeforeUnmount(() => {
  editor.value?.destroy()
})
</script>

<template>
  <div class="rich-text-editor" :class="{ 'is-readonly': !editable }">
    <EditorToolbar v-if="editable" :editor="editor" />
    <EditorContent :editor="editor" class="editor-content" />
    <div v-if="editable && charLimit > 0" class="char-counter" :class="{ over: isOverLimit }">
      {{ charCount }} / {{ charLimit }}
    </div>
  </div>
</template>

<style scoped>
.rich-text-editor {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  overflow: hidden;
  transition: border-color var(--transition-fast);
}

.rich-text-editor:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px var(--input-ring);
}

.is-readonly {
  border-color: transparent;
  background: transparent;
}

.is-readonly:focus-within {
  border-color: transparent;
  box-shadow: none;
}

.editor-content {
  padding: 12px 16px;
  min-height: 120px;
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  color: var(--color-text);
}

.editor-content :deep(.tiptap) {
  outline: none;
  min-height: 96px;
}

.editor-content :deep(.tiptap p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  float: left;
  color: var(--color-text-muted);
  pointer-events: none;
  height: 0;
}

.editor-content :deep(.tiptap p) {
  margin: 0 0 0.5em;
}

.editor-content :deep(.tiptap p:last-child) {
  margin-bottom: 0;
}

.editor-content :deep(.tiptap h2) {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  margin: 1em 0 0.5em;
  line-height: var(--leading-tight);
}

.editor-content :deep(.tiptap h3) {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  margin: 0.75em 0 0.4em;
  line-height: var(--leading-tight);
}

.editor-content :deep(.tiptap h2:first-child),
.editor-content :deep(.tiptap h3:first-child) {
  margin-top: 0;
}

.editor-content :deep(.tiptap ul),
.editor-content :deep(.tiptap ol) {
  padding-left: 1.5em;
  margin: 0.5em 0;
}

.editor-content :deep(.tiptap li) {
  margin: 0.2em 0;
}

.editor-content :deep(.tiptap blockquote) {
  border-left: 3px solid var(--color-primary);
  padding-left: 1em;
  margin: 0.5em 0;
  color: var(--color-text-secondary);
}

.editor-content :deep(.tiptap code) {
  background: var(--color-primary-light);
  color: var(--color-primary);
  padding: 0.15em 0.3em;
  border-radius: var(--radius-sm);
  font-family: var(--font-mono);
  font-size: 0.9em;
}

.editor-content :deep(.tiptap pre) {
  background: var(--color-navy);
  color: var(--color-text-on-dark);
  padding: 1em;
  border-radius: var(--radius);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  overflow-x: auto;
  margin: 0.5em 0;
}

.editor-content :deep(.tiptap pre code) {
  background: none;
  color: inherit;
  padding: 0;
  border-radius: 0;
  font-size: inherit;
}

.editor-content :deep(.tiptap strong) {
  font-weight: var(--font-bold);
}

.editor-content :deep(.tiptap hr) {
  border: none;
  border-top: 1px solid var(--color-border);
  margin: 1em 0;
}

.editor-content :deep(.editor-link) {
  color: var(--color-primary);
  text-decoration: underline;
  cursor: pointer;
}

.char-counter {
  padding: 4px 14px 8px;
  text-align: right;
  font-size: 11px;
  color: var(--color-text-muted);
}

.char-counter.over {
  color: var(--color-error);
  font-weight: 500;
}
</style>
