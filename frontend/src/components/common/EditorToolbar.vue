<script setup>
const props = defineProps({
  editor: { type: Object, default: null },
})

const groups = [
  [
    { action: 'bold', label: 'B', title: 'Bold (Ctrl+B)', style: 'font-bold' },
    { action: 'italic', label: 'I', title: 'Italic (Ctrl+I)', style: 'italic' },
  ],
  [
    { action: 'bulletList', label: '•', title: 'Bullet List', style: '' },
    { action: 'orderedList', label: '1.', title: 'Ordered List', style: '' },
  ],
]

function toggle(action) {
  if (!props.editor) return
  const chain = props.editor.chain().focus()
  const commands = {
    bold: () => chain.toggleBold().run(),
    italic: () => chain.toggleItalic().run(),
    bulletList: () => chain.toggleBulletList().run(),
    orderedList: () => chain.toggleOrderedList().run(),
  }
  commands[action]?.()
}

function isActive(action) {
  if (!props.editor) return false
  return props.editor.isActive(action)
}
</script>

<template>
  <div v-if="editor" class="editor-toolbar">
    <template v-for="(group, gi) in groups" :key="gi">
      <div v-if="gi > 0" class="toolbar-divider" />
      <button
        v-for="btn in group"
        :key="btn.action"
        type="button"
        :title="btn.title"
        :class="['toolbar-btn', btn.style, { active: isActive(btn.action) }]"
        @click="toggle(btn.action)"
      >
        {{ btn.label }}
      </button>
    </template>
  </div>
</template>

<style scoped>
.editor-toolbar {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 4px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg, #fafafa);
  border-radius: var(--radius-lg) var(--radius-lg) 0 0;
}

.toolbar-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: var(--radius-sm);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: background var(--transition-fast), color var(--transition-fast);
}

.toolbar-btn:hover {
  background: var(--color-tint);
  color: var(--color-text);
}

.toolbar-btn.active {
  background: var(--color-primary-light);
  color: var(--color-primary);
}

.toolbar-divider {
  width: 1px;
  height: 18px;
  background: var(--color-border);
  margin: 0 4px;
}
</style>
