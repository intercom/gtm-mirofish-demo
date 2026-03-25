<script setup>
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Link from '@tiptap/extension-link'
import Placeholder from '@tiptap/extension-placeholder'
import { watch } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: 'Start writing...' },
  editable: { type: Boolean, default: true },
})

const emit = defineEmits(['update:modelValue'])

const editor = useEditor({
  content: props.modelValue,
  editable: props.editable,
  extensions: [
    StarterKit.configure({
      heading: { levels: [2, 3] },
    }),
    Link.configure({
      openOnClick: false,
      HTMLAttributes: { class: 'editor-link' },
    }),
    Placeholder.configure({
      placeholder: props.placeholder,
    }),
  ],
  onUpdate: ({ editor }) => {
    emit('update:modelValue', editor.getHTML())
  },
})

watch(() => props.modelValue, (val) => {
  if (editor.value && val !== editor.value.getHTML()) {
    editor.value.commands.setContent(val, false)
  }
})

watch(() => props.editable, (val) => {
  editor.value?.setEditable(val)
})

function toggleLink() {
  if (!editor.value) return
  if (editor.value.isActive('link')) {
    editor.value.chain().focus().unsetLink().run()
    return
  }
  const url = window.prompt('Enter URL')
  if (url) {
    editor.value.chain().focus().setLink({ href: url }).run()
  }
}
</script>

<template>
  <div class="rich-text-editor" :class="{ 'is-readonly': !editable }">
    <div v-if="editable" class="toolbar">
      <button
        type="button"
        @click="editor?.chain().focus().toggleBold().run()"
        :class="{ active: editor?.isActive('bold') }"
        title="Bold"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M6 4h8a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"/><path d="M6 12h9a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z"/>
        </svg>
      </button>
      <button
        type="button"
        @click="editor?.chain().focus().toggleItalic().run()"
        :class="{ active: editor?.isActive('italic') }"
        title="Italic"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="19" y1="4" x2="10" y2="4"/><line x1="14" y1="20" x2="5" y2="20"/><line x1="15" y1="4" x2="9" y2="20"/>
        </svg>
      </button>

      <span class="divider" />

      <button
        type="button"
        @click="editor?.chain().focus().toggleHeading({ level: 2 }).run()"
        :class="{ active: editor?.isActive('heading', { level: 2 }) }"
        title="Heading"
      >
        H2
      </button>
      <button
        type="button"
        @click="editor?.chain().focus().toggleHeading({ level: 3 }).run()"
        :class="{ active: editor?.isActive('heading', { level: 3 }) }"
        title="Subheading"
      >
        H3
      </button>

      <span class="divider" />

      <button
        type="button"
        @click="editor?.chain().focus().toggleBulletList().run()"
        :class="{ active: editor?.isActive('bulletList') }"
        title="Bullet list"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/>
          <circle cx="3" cy="6" r="1" fill="currentColor"/><circle cx="3" cy="12" r="1" fill="currentColor"/><circle cx="3" cy="18" r="1" fill="currentColor"/>
        </svg>
      </button>
      <button
        type="button"
        @click="editor?.chain().focus().toggleOrderedList().run()"
        :class="{ active: editor?.isActive('orderedList') }"
        title="Numbered list"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="10" y1="6" x2="21" y2="6"/><line x1="10" y1="12" x2="21" y2="12"/><line x1="10" y1="18" x2="21" y2="18"/>
          <text x="1" y="8" font-size="8" fill="currentColor" stroke="none" font-family="system-ui">1</text>
          <text x="1" y="14" font-size="8" fill="currentColor" stroke="none" font-family="system-ui">2</text>
          <text x="1" y="20" font-size="8" fill="currentColor" stroke="none" font-family="system-ui">3</text>
        </svg>
      </button>

      <span class="divider" />

      <button
        type="button"
        @click="toggleLink"
        :class="{ active: editor?.isActive('link') }"
        title="Link"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>
          <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>
        </svg>
      </button>

      <span class="divider" />

      <button
        type="button"
        @click="editor?.chain().focus().toggleBlockquote().run()"
        :class="{ active: editor?.isActive('blockquote') }"
        title="Quote"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V21z"/>
          <path d="M15 21c3 0 7-1 7-8V5c0-1.25-.757-2.017-2-2h-4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2h.75c0 2.25.25 4-2.75 4v3z"/>
        </svg>
      </button>
    </div>

    <EditorContent :editor="editor" class="editor-content" />
  </div>
</template>

<style scoped>
.rich-text-editor {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: var(--color-surface);
  overflow: hidden;
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

.toolbar {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 6px 8px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg);
  flex-wrap: wrap;
}

.toolbar button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  height: 30px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  transition: all var(--transition-fast);
}

.toolbar button:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.toolbar button.active {
  background: var(--color-primary);
  color: white;
}

.divider {
  width: 1px;
  height: 20px;
  background: var(--color-border);
  margin: 0 4px;
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

.editor-content :deep(.tiptap p) {
  margin: 0 0 0.5em;
}

.editor-content :deep(.tiptap p:last-child) {
  margin-bottom: 0;
}

.editor-content :deep(.tiptap h2) {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  margin: 0.75em 0 0.4em;
  color: var(--color-text);
}

.editor-content :deep(.tiptap h3) {
  font-size: var(--text-base);
  font-weight: var(--font-semibold);
  margin: 0.6em 0 0.3em;
  color: var(--color-text);
}

.editor-content :deep(.tiptap h2:first-child),
.editor-content :deep(.tiptap h3:first-child) {
  margin-top: 0;
}

.editor-content :deep(.tiptap ul),
.editor-content :deep(.tiptap ol) {
  padding-left: 1.25em;
  margin: 0.4em 0;
}

.editor-content :deep(.tiptap li) {
  margin: 0.15em 0;
}

.editor-content :deep(.tiptap blockquote) {
  border-left: 3px solid var(--color-primary);
  padding-left: 1em;
  margin: 0.5em 0;
  color: var(--color-text-secondary);
}

.editor-content :deep(.editor-link) {
  color: var(--color-primary);
  text-decoration: underline;
  cursor: pointer;
}

.editor-content :deep(.tiptap p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  color: var(--color-text-muted);
  pointer-events: none;
  float: left;
  height: 0;
}
</style>
