<script setup>
import { watch, onBeforeUnmount } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Link from '@tiptap/extension-link'
import Placeholder from '@tiptap/extension-placeholder'

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
  placeholder: {
    type: String,
    default: 'Start typing...',
  },
  editable: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['update:modelValue'])

const editor = useEditor({
  extensions: [
    StarterKit.configure({
      heading: { levels: [2, 3] },
    }),
    Link.configure({
      openOnClick: false,
      HTMLAttributes: { class: 'editor-link' },
    }),
    Placeholder.configure({ placeholder: props.placeholder }),
  ],
  content: props.modelValue,
  editable: props.editable,
  onUpdate({ editor }) {
    emit('update:modelValue', editor.getHTML())
  },
})

watch(() => props.modelValue, (value) => {
  if (!editor.value) return
  const current = editor.value.getHTML()
  if (current === value) return
  editor.value.commands.setContent(value, false)
})

watch(() => props.editable, (value) => {
  editor.value?.setEditable(value)
})

onBeforeUnmount(() => {
  editor.value?.destroy()
})

function toggleMark(mark) {
  editor.value?.chain().focus().toggleMark(mark).run()
}

function toggleNode(type, attrs) {
  if (type === 'bulletList') {
    editor.value?.chain().focus().toggleBulletList().run()
  } else if (type === 'orderedList') {
    editor.value?.chain().focus().toggleOrderedList().run()
  } else if (type === 'blockquote') {
    editor.value?.chain().focus().toggleBlockquote().run()
  } else if (type === 'codeBlock') {
    editor.value?.chain().focus().toggleCodeBlock().run()
  } else if (type === 'heading') {
    editor.value?.chain().focus().toggleHeading(attrs).run()
  }
}

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

function isActive(type, attrs) {
  return editor.value?.isActive(type, attrs) ?? false
}
</script>

<template>
  <div class="rich-text-editor" :class="{ 'is-readonly': !editable }">
    <div v-if="editable && editor" class="toolbar">
      <div class="toolbar-group">
        <button
          type="button"
          :class="['toolbar-btn', { active: isActive('bold') }]"
          title="Bold"
          @click="toggleMark('bold')"
        >
          <strong>B</strong>
        </button>
        <button
          type="button"
          :class="['toolbar-btn', { active: isActive('italic') }]"
          title="Italic"
          @click="toggleMark('italic')"
        >
          <em>I</em>
        </button>
        <button
          type="button"
          :class="['toolbar-btn', { active: isActive('strike') }]"
          title="Strikethrough"
          @click="toggleMark('strike')"
        >
          <s>S</s>
        </button>
        <button
          type="button"
          :class="['toolbar-btn', { active: isActive('code') }]"
          title="Inline code"
          @click="toggleMark('code')"
        >
          &lt;/&gt;
        </button>
      </div>

      <div class="toolbar-divider" />

      <div class="toolbar-group">
        <button
          type="button"
          :class="['toolbar-btn', { active: isActive('heading', { level: 2 }) }]"
          title="Heading"
          @click="toggleNode('heading', { level: 2 })"
        >
          H2
        </button>
        <button
          type="button"
          :class="['toolbar-btn', { active: isActive('heading', { level: 3 }) }]"
          title="Subheading"
          @click="toggleNode('heading', { level: 3 })"
        >
          H3
        </button>
      </div>

      <div class="toolbar-divider" />

      <div class="toolbar-group">
        <button
          type="button"
          :class="['toolbar-btn', { active: isActive('bulletList') }]"
          title="Bullet list"
          @click="toggleNode('bulletList')"
        >
          &#8226;
        </button>
        <button
          type="button"
          :class="['toolbar-btn', { active: isActive('orderedList') }]"
          title="Numbered list"
          @click="toggleNode('orderedList')"
        >
          1.
        </button>
        <button
          type="button"
          :class="['toolbar-btn', { active: isActive('blockquote') }]"
          title="Quote"
          @click="toggleNode('blockquote')"
        >
          &#x201C;
        </button>
        <button
          type="button"
          :class="['toolbar-btn', { active: isActive('codeBlock') }]"
          title="Code block"
          @click="toggleNode('codeBlock')"
        >
          { }
        </button>
      </div>

      <div class="toolbar-divider" />

      <div class="toolbar-group">
        <button
          type="button"
          :class="['toolbar-btn', { active: isActive('link') }]"
          title="Link"
          @click="toggleLink"
        >
          &#x1F517;
        </button>
      </div>
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

.toolbar {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 6px 8px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg);
}

.toolbar-group {
  display: flex;
  gap: 1px;
}

.toolbar-divider {
  width: 1px;
  height: 20px;
  margin: 0 4px;
  background: var(--color-border);
}

.toolbar-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: var(--text-xs);
  font-family: var(--font-family);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.toolbar-btn:hover {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.toolbar-btn.active {
  background: var(--color-primary-light);
  color: var(--color-primary);
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
</style>
