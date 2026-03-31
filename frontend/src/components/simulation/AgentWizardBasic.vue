<script setup>
import { ref, watch } from 'vue'
import RichTextEditor from '../common/RichTextEditor.vue'

const props = defineProps({
  agent: { type: Object, default: () => ({}) },
})

const emit = defineEmits(['update'])

const name = ref(props.agent.name || '')
const role = ref(props.agent.role || '')
const company = ref(props.agent.company || '')
const backstory = ref(props.agent.backstory || '')

watch([name, role, company, backstory], () => {
  emit('update', {
    name: name.value,
    role: role.value,
    company: company.value,
    backstory: backstory.value,
  })
})

watch(() => props.agent, (a) => {
  if (a.name !== undefined) name.value = a.name
  if (a.role !== undefined) role.value = a.role
  if (a.company !== undefined) company.value = a.company
  if (a.backstory !== undefined) backstory.value = a.backstory
}, { deep: true })

const inputClasses =
  'w-full bg-[var(--input-bg)] border border-[var(--input-border)] rounded-lg px-3 py-2 text-sm text-[var(--input-text)] placeholder:text-[var(--input-placeholder)] focus:outline-none focus:border-[var(--color-primary)] focus:ring-2 focus:ring-[var(--input-ring)] transition-colors'
</script>

<template>
  <div class="space-y-4">
    <div>
      <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">Name</label>
      <input v-model="name" :class="inputClasses" placeholder="Agent name" />
    </div>

    <div class="grid grid-cols-2 gap-3">
      <div>
        <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">Role</label>
        <input v-model="role" :class="inputClasses" placeholder="e.g. VP of Support" />
      </div>
      <div>
        <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">Company</label>
        <input v-model="company" :class="inputClasses" placeholder="e.g. Intercom" />
      </div>
    </div>

    <div>
      <label class="block text-xs font-semibold text-[var(--color-text)] mb-1.5">Backstory</label>
      <RichTextEditor
        v-model="backstory"
        placeholder="Describe this agent's background, experience, and perspective..."
        :char-limit="500"
      />
    </div>
  </div>
</template>
