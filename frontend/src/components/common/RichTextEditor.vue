<script setup>
import { watch, onBeforeUnmount, computed } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import CharacterCount from '@tiptap/extension-character-count'
import EditorToolbar from './EditorToolbar.vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  charLimit: { type: Number, default: 0 },
  editable: { type: Boolean, default: true },
})

const emit = defineEmits(['update:modelValue'])

const extensions = [
  StarterKit.configure({
    heading: false,
    codeBlock: false,
    blockquote: false,
    horizontalRule: false,
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
  <div class="rich-text-editor" :class="{ 'read-only': !editable }">
    <EditorToolbar v-if="editable" :editor="editor" />
    <EditorContent :editor="editor" class="editor-content" />
    <div v-if="editable && charLimit > 0" class="char-counter" :class="{ over: isOverLimit }">
      {{ charCount }} / {{ charLimit }}
    </div>
  </div>
</template>

<style scoped>
.rich-text-editor {
  border: 1px solid var(--input-border);
  border-radius: var(--radius-lg);
  background: var(--input-bg);
  transition: border-color var(--transition-fast);
}

.rich-text-editor:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 2px var(--input-ring);
}

.rich-text-editor.read-only {
  border: none;
  background: transparent;
}

.editor-content {
  padding: 10px 14px;
  min-height: 80px;
  font-size: var(--text-sm);
  color: var(--input-text);
  line-height: var(--leading-relaxed);
}

.editor-content :deep(.tiptap) {
  outline: none;
  min-height: 60px;
}

.editor-content :deep(.tiptap p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  float: left;
  color: var(--input-placeholder);
  pointer-events: none;
  height: 0;
}

.editor-content :deep(.tiptap p) {
  margin: 0 0 0.5em;
}

.editor-content :deep(.tiptap p:last-child) {
  margin-bottom: 0;
}

.editor-content :deep(.tiptap ul),
.editor-content :deep(.tiptap ol) {
  padding-left: 1.25em;
  margin: 0.25em 0;
}

.editor-content :deep(.tiptap li) {
  margin: 0.15em 0;
}

.editor-content :deep(.tiptap strong) {
  font-weight: 600;
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
