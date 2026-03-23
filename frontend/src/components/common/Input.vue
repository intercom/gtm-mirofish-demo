<script setup>
const props = defineProps({
  modelValue: {
    type: [String, Number],
    default: '',
  },
  type: {
    type: String,
    default: 'text',
    validator: (v) => ['text', 'select', 'textarea', 'email', 'password', 'number', 'url'].includes(v),
  },
  label: String,
  placeholder: String,
  disabled: Boolean,
  rows: {
    type: Number,
    default: 4,
  },
  options: {
    type: Array,
    default: () => [],
  },
})

defineEmits(['update:modelValue'])

const inputClasses =
  'w-full border border-black/10 rounded-lg px-4 py-2 text-sm bg-white text-[#050505] placeholder-[#888] focus:ring-2 focus:ring-[#2068FF] focus:border-transparent outline-none transition-colors disabled:opacity-50 disabled:cursor-not-allowed'
</script>

<template>
  <div>
    <label v-if="label" class="block text-xs uppercase tracking-wider text-[#888] mb-2">
      {{ label }}
    </label>

    <select
      v-if="type === 'select'"
      :value="modelValue"
      :disabled="disabled"
      :class="inputClasses"
      @change="$emit('update:modelValue', $event.target.value)"
    >
      <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
      <option v-for="opt in options" :key="opt.value ?? opt" :value="opt.value ?? opt">
        {{ opt.label ?? opt }}
      </option>
    </select>

    <textarea
      v-else-if="type === 'textarea'"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :rows="rows"
      :class="[inputClasses, 'resize-y']"
      @input="$emit('update:modelValue', $event.target.value)"
    />

    <input
      v-else
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      :class="inputClasses"
      @input="$emit('update:modelValue', $event.target.value)"
    />
  </div>
</template>
