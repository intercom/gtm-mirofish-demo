<script setup>
import { watch, onBeforeUnmount } from 'vue'
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Underline from '@tiptap/extension-underline'

const props = defineProps({
  modelValue: { type: String, default: '' },
})

const emit = defineEmits(['update:modelValue'])

const editor = useEditor({
  content: props.modelValue,
  extensions: [
    StarterKit.configure({
      heading: { levels: [2, 3, 4] },
    }),
    Underline,
  ],
  editorProps: {
    attributes: {
      class: 'report-editor-content focus:outline-none min-h-[200px] px-4 py-3',
    },
  },
  onUpdate: ({ editor: ed }) => {
    emit('update:modelValue', ed.getHTML())
  },
})

watch(() => props.modelValue, (val) => {
  if (editor.value && editor.value.getHTML() !== val) {
    editor.value.commands.setContent(val, false)
  }
})

onBeforeUnmount(() => {
  editor.value?.destroy()
})

function isActive(name, attrs) {
  return editor.value?.isActive(name, attrs) ?? false
}

function run(command) {
  command(editor.value?.chain().focus())?.run()
}

const toolbarGroups = [
  [
    { label: 'Bold', icon: 'B', action: (c) => c.toggleBold(), active: 'bold', style: 'font-weight:700' },
    { label: 'Italic', icon: 'I', action: (c) => c.toggleItalic(), active: 'italic', style: 'font-style:italic' },
    { label: 'Underline', icon: 'U', action: (c) => c.toggleUnderline(), active: 'underline', style: 'text-decoration:underline' },
    { label: 'Strike', icon: 'S', action: (c) => c.toggleStrike(), active: 'strike', style: 'text-decoration:line-through' },
  ],
  [
    { label: 'Heading 2', icon: 'H2', action: (c) => c.toggleHeading({ level: 2 }), active: 'heading', attrs: { level: 2 } },
    { label: 'Heading 3', icon: 'H3', action: (c) => c.toggleHeading({ level: 3 }), active: 'heading', attrs: { level: 3 } },
  ],
  [
    { label: 'Bullet List', icon: 'ul', action: (c) => c.toggleBulletList(), active: 'bulletList', svg: 'list-bullet' },
    { label: 'Ordered List', icon: 'ol', action: (c) => c.toggleOrderedList(), active: 'orderedList', svg: 'list-ordered' },
    { label: 'Blockquote', icon: 'bq', action: (c) => c.toggleBlockquote(), active: 'blockquote', svg: 'quote' },
  ],
  [
    { label: 'Horizontal Rule', icon: '—', action: (c) => c.setHorizontalRule() },
  ],
]
</script>

<template>
  <div class="rich-text-editor border border-[var(--color-border)] rounded-lg overflow-hidden bg-[var(--color-surface)]">
    <!-- Toolbar -->
    <div v-if="editor" class="toolbar flex flex-wrap items-center gap-0.5 px-2 py-1.5 border-b border-[var(--color-border)] bg-[var(--color-tint)]">
      <template v-for="(group, gi) in toolbarGroups" :key="gi">
        <div v-if="gi > 0" class="w-px h-5 bg-[var(--color-border)] mx-1" />
        <button
          v-for="btn in group"
          :key="btn.label"
          :title="btn.label"
          @click="run(btn.action)"
          class="toolbar-btn w-7 h-7 flex items-center justify-center rounded text-xs transition-colors"
          :class="isActive(btn.active, btn.attrs)
            ? 'bg-[#2068FF] text-white'
            : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-border)]'"
        >
          <!-- SVG icons for list/quote -->
          <template v-if="btn.svg === 'list-bullet'">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" />
            </svg>
          </template>
          <template v-else-if="btn.svg === 'list-ordered'">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 6h14M7 12h14M7 18h14M3 6v2m0 4v2m0 4v2" />
            </svg>
          </template>
          <template v-else-if="btn.svg === 'quote'">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M4.583 17.321C3.553 16.227 3 15 3 13.011c0-3.5 2.457-6.637 6.03-8.188l.893 1.378c-3.335 1.804-3.987 4.145-4.247 5.621.537-.278 1.24-.375 1.929-.311 1.804.167 3.226 1.648 3.226 3.489a3.5 3.5 0 01-3.5 3.5 3.871 3.871 0 01-2.748-1.179zm10 0C13.553 16.227 13 15 13 13.011c0-3.5 2.457-6.637 6.03-8.188l.893 1.378c-3.335 1.804-3.987 4.145-4.247 5.621.537-.278 1.24-.375 1.929-.311 1.804.167 3.226 1.648 3.226 3.489a3.5 3.5 0 01-3.5 3.5 3.871 3.871 0 01-2.748-1.179z" />
            </svg>
          </template>
          <template v-else>
            <span :style="btn.style">{{ btn.icon }}</span>
          </template>
        </button>
      </template>
    </div>

    <!-- Editor area -->
    <EditorContent :editor="editor" />
  </div>
</template>

<style scoped>
.toolbar-btn {
  cursor: pointer;
  border: none;
  background: none;
  font-family: inherit;
}

/* Editor content styling — mirrors the report-content read-only styles */
.rich-text-editor :deep(.report-editor-content) {
  font-size: 0.875rem;
  line-height: 1.625;
  color: var(--color-text-secondary);
}
.rich-text-editor :deep(.report-editor-content h2) {
  font-size: 1.25rem;
  font-weight: 600;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
  color: var(--color-text);
}
.rich-text-editor :deep(.report-editor-content h3) {
  font-size: 1.125rem;
  font-weight: 600;
  margin-top: 1rem;
  margin-bottom: 0.5rem;
  color: var(--color-text);
}
.rich-text-editor :deep(.report-editor-content h4) {
  font-size: 1rem;
  font-weight: 600;
  margin-top: 0.75rem;
  margin-bottom: 0.5rem;
  color: var(--color-text);
}
.rich-text-editor :deep(.report-editor-content p) {
  margin-bottom: 0.75rem;
}
.rich-text-editor :deep(.report-editor-content ul) {
  list-style-type: disc;
  margin-bottom: 0.75rem;
  padding-left: 1.5rem;
}
.rich-text-editor :deep(.report-editor-content ol) {
  list-style-type: decimal;
  margin-bottom: 0.75rem;
  padding-left: 1.5rem;
}
.rich-text-editor :deep(.report-editor-content li) {
  margin-bottom: 0.25rem;
}
.rich-text-editor :deep(.report-editor-content li p) {
  margin-bottom: 0;
}
.rich-text-editor :deep(.report-editor-content strong) {
  font-weight: 600;
  color: var(--color-text);
}
.rich-text-editor :deep(.report-editor-content blockquote) {
  border-left: 3px solid var(--color-primary);
  padding-left: 1rem;
  margin: 1rem 0;
  color: var(--color-text-secondary);
  font-style: italic;
}
.rich-text-editor :deep(.report-editor-content hr) {
  border: none;
  border-top: 1px solid var(--color-border);
  margin: 1.5rem 0;
}
.rich-text-editor :deep(.report-editor-content code) {
  background: var(--color-tint);
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.8125rem;
}
</style>
