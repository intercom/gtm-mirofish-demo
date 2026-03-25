<script setup>
import { computed } from 'vue'

const props = defineProps({
  editor: { type: Object, default: null },
})

const groups = computed(() => {
  if (!props.editor) return []
  const e = props.editor
  return [
    [
      { label: 'Bold', shortcut: 'Ctrl+B', icon: 'bold', active: e.isActive('bold'), action: () => e.chain().focus().toggleBold().run() },
      { label: 'Italic', shortcut: 'Ctrl+I', icon: 'italic', active: e.isActive('italic'), action: () => e.chain().focus().toggleItalic().run() },
    ],
    [
      { label: 'Heading 1', shortcut: 'Ctrl+Alt+1', icon: 'h1', active: e.isActive('heading', { level: 1 }), action: () => e.chain().focus().toggleHeading({ level: 1 }).run() },
      { label: 'Heading 2', shortcut: 'Ctrl+Alt+2', icon: 'h2', active: e.isActive('heading', { level: 2 }), action: () => e.chain().focus().toggleHeading({ level: 2 }).run() },
      { label: 'Heading 3', shortcut: 'Ctrl+Alt+3', icon: 'h3', active: e.isActive('heading', { level: 3 }), action: () => e.chain().focus().toggleHeading({ level: 3 }).run() },
    ],
    [
      { label: 'Bullet List', shortcut: 'Ctrl+Shift+8', icon: 'bulletList', active: e.isActive('bulletList'), action: () => e.chain().focus().toggleBulletList().run() },
      { label: 'Ordered List', shortcut: 'Ctrl+Shift+7', icon: 'orderedList', active: e.isActive('orderedList'), action: () => e.chain().focus().toggleOrderedList().run() },
    ],
    [
      { label: 'Code Block', shortcut: 'Ctrl+Alt+C', icon: 'codeBlock', active: e.isActive('codeBlock'), action: () => e.chain().focus().toggleCodeBlock().run() },
      { label: 'Link', shortcut: 'Ctrl+K', icon: 'link', active: e.isActive('link'), action: () => toggleLink() },
    ],
    [
      { label: 'Undo', shortcut: 'Ctrl+Z', icon: 'undo', active: false, action: () => e.chain().focus().undo().run() },
      { label: 'Redo', shortcut: 'Ctrl+Shift+Z', icon: 'redo', active: false, action: () => e.chain().focus().redo().run() },
    ],
  ]
})

function toggleLink() {
  const e = props.editor
  if (!e) return
  if (e.isActive('link')) {
    e.chain().focus().unsetLink().run()
    return
  }
  const url = window.prompt('Enter URL')
  if (url) {
    e.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
  }
}
</script>

<template>
  <div
    v-if="editor"
    class="editor-toolbar"
    role="toolbar"
    aria-label="Text formatting"
  >
    <template v-for="(group, gi) in groups" :key="gi">
      <div v-if="gi > 0" class="editor-toolbar__divider" />
      <button
        v-for="btn in group"
        :key="btn.icon"
        type="button"
        class="editor-toolbar__btn"
        :class="{ 'editor-toolbar__btn--active': btn.active }"
        :title="`${btn.label} (${btn.shortcut})`"
        :aria-label="btn.label"
        :aria-pressed="btn.active"
        @click="btn.action"
      >
        <!-- Bold -->
        <svg v-if="btn.icon === 'bold'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M6 4h8a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z" /><path d="M6 12h9a4 4 0 0 1 4 4 4 4 0 0 1-4 4H6z" />
        </svg>
        <!-- Italic -->
        <svg v-else-if="btn.icon === 'italic'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <line x1="19" y1="4" x2="10" y2="4" /><line x1="14" y1="20" x2="5" y2="20" /><line x1="15" y1="4" x2="9" y2="20" />
        </svg>
        <!-- H1 -->
        <svg v-else-if="btn.icon === 'h1'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 12h8" /><path d="M4 18V6" /><path d="M12 18V6" /><path d="M17 12l3-2v10" />
        </svg>
        <!-- H2 -->
        <svg v-else-if="btn.icon === 'h2'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 12h8" /><path d="M4 18V6" /><path d="M12 18V6" /><path d="M21 18h-4c0-4 4-3 4-6 0-1.5-2-2.5-4-1" />
        </svg>
        <!-- H3 -->
        <svg v-else-if="btn.icon === 'h3'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 12h8" /><path d="M4 18V6" /><path d="M12 18V6" /><path d="M17.5 10.5c1.7-1 3.5 0 3.5 1.5a2 2 0 0 1-2 2" /><path d="M17 17.5c2 1.5 4 .3 4-1.5a2 2 0 0 0-2-2" />
        </svg>
        <!-- Bullet List -->
        <svg v-else-if="btn.icon === 'bulletList'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="9" y1="6" x2="20" y2="6" /><line x1="9" y1="12" x2="20" y2="12" /><line x1="9" y1="18" x2="20" y2="18" />
          <circle cx="4" cy="6" r="1" fill="currentColor" /><circle cx="4" cy="12" r="1" fill="currentColor" /><circle cx="4" cy="18" r="1" fill="currentColor" />
        </svg>
        <!-- Ordered List -->
        <svg v-else-if="btn.icon === 'orderedList'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="10" y1="6" x2="21" y2="6" /><line x1="10" y1="12" x2="21" y2="12" /><line x1="10" y1="18" x2="21" y2="18" />
          <path d="M4 6h1v4" /><path d="M4 10h2" /><path d="M6 18H4c0-1 2-2 2-3s-1-1.5-2-1" />
        </svg>
        <!-- Code Block -->
        <svg v-else-if="btn.icon === 'codeBlock'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
        </svg>
        <!-- Link -->
        <svg v-else-if="btn.icon === 'link'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" /><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
        </svg>
        <!-- Undo -->
        <svg v-else-if="btn.icon === 'undo'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 7v6h6" /><path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6 2.3L3 13" />
        </svg>
        <!-- Redo -->
        <svg v-else-if="btn.icon === 'redo'" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 7v6h-6" /><path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6 2.3L21 13" />
        </svg>
      </button>
    </template>
  </div>
</template>

<style scoped>
.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 4px 6px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-bottom: none;
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}

.editor-toolbar__divider {
  width: 1px;
  height: 20px;
  margin: 0 4px;
  background: var(--color-border);
  flex-shrink: 0;
}

.editor-toolbar__btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: background var(--transition-fast), color var(--transition-fast);
}

.editor-toolbar__btn:hover {
  background: var(--color-tint);
  color: var(--color-text);
}

.editor-toolbar__btn--active {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.editor-toolbar__btn--active:hover {
  background: var(--color-primary-tint-hover);
  color: var(--color-primary);
}
</style>
