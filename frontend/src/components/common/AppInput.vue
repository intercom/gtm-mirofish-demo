<script setup>
import { ref, watch, useId } from 'vue'

const props = defineProps({
  type: {
    type: String,
    default: 'text',
    validator: (v) => ['text', 'select', 'textarea'].includes(v),
  },
  modelValue: [String, Number],
  label: String,
  placeholder: String,
  error: String,
  options: Array,
  rows: {
    type: Number,
    default: 4,
  },
})

defineEmits(['update:modelValue'])

const shaking = ref(false)
const inputId = `input-${useId()}`
const errorId = `input-error-${useId()}`

watch(() => props.error, (val, oldVal) => {
  if (val && val !== oldVal) {
    shaking.value = true
    setTimeout(() => { shaking.value = false }, 400)
  }
})

const inputClasses =
  'input-interactive w-full bg-[--color-surface] border border-[--color-border] rounded-lg px-3 py-2 text-sm text-[--color-text] placeholder:text-[--color-text-muted] focus:outline-none focus:border-[--color-primary] focus:ring-1 focus:ring-[--color-primary] focus-ring-pulse'
</script>

<template>
  <div>
    <label v-if="label" :for="inputId" class="block text-xs font-semibold text-[--color-text] mb-1.5">
      {{ label }}
    </label>

    <select
      v-if="type === 'select'"
      :id="inputId"
      :value="modelValue"
      :class="[inputClasses, error && 'border-red-500', shaking && 'animate-shake']"
      :aria-invalid="error ? 'true' : undefined"
      :aria-describedby="error ? errorId : undefined"
      @change="$emit('update:modelValue', $event.target.value)"
    >
      <option v-if="placeholder" value="" disabled>{{ placeholder }}</option>
      <option v-for="opt in options" :key="opt.value ?? opt" :value="opt.value ?? opt">
        {{ opt.label ?? opt }}
      </option>
    </select>

    <textarea
      v-else-if="type === 'textarea'"
      :id="inputId"
      :value="modelValue"
      :placeholder="placeholder"
      :rows="rows"
      :class="[inputClasses, 'resize-y', error && 'border-red-500', shaking && 'animate-shake']"
      :aria-invalid="error ? 'true' : undefined"
      :aria-describedby="error ? errorId : undefined"
      @input="$emit('update:modelValue', $event.target.value)"
    />

    <input
      v-else
      :id="inputId"
      type="text"
      :value="modelValue"
      :placeholder="placeholder"
      :class="[inputClasses, error && 'border-red-500', shaking && 'animate-shake']"
      :aria-invalid="error ? 'true' : undefined"
      :aria-describedby="error ? errorId : undefined"
      @input="$emit('update:modelValue', $event.target.value)"
    />

    <p v-if="error" :id="errorId" role="alert" class="text-xs text-red-500 mt-1">{{ error }}</p>
  </div>
</template>
