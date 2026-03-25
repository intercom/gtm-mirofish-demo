<script setup>
import { ref, computed } from 'vue'
import { useReportTheme } from '../../composables/useReportTheme'

const {
  presets,
  activePresetId,
  resolvedTheme,
  setPreset,
  setCustom,
  resetCustom,
} = useReportTheme()

const presetList = computed(() => Object.values(presets))
const showCustom = ref(false)

const FONT_OPTIONS = [
  { label: 'System Default', value: "system-ui, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" },
  { label: 'Georgia (Serif)', value: "'Georgia', 'Times New Roman', serif" },
  { label: 'Helvetica', value: "'Helvetica Neue', Helvetica, Arial, sans-serif" },
  { label: 'Monospace', value: "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace" },
]

const SIZE_OPTIONS = [
  { label: 'Small', heading: '1.25rem', body: '0.8125rem' },
  { label: 'Medium', heading: '1.5rem', body: '0.875rem' },
  { label: 'Large', heading: '1.625rem', body: '0.9375rem' },
]

const currentSizeLabel = computed(() => {
  const match = SIZE_OPTIONS.find(s => s.heading === resolvedTheme.value.headingSize)
  return match ? match.label : 'Custom'
})

function selectSize(opt) {
  setCustom('headingSize', opt.heading)
  setCustom('bodySize', opt.body)
}

function handleReset() {
  resetCustom()
  showCustom.value = false
}

const PRESET_COLORS = {
  intercom: '#2068FF',
  corporate: '#050505',
  minimal: '#555555',
  colorful: '#ff5600',
}
</script>

<template>
  <div class="theme-configurator">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-sm font-semibold text-[var(--color-text)]">Report Theme</h3>
      <button
        v-if="showCustom"
        @click="handleReset"
        class="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text-secondary)] transition-colors"
      >
        Reset
      </button>
    </div>

    <!-- Preset Selection -->
    <div class="grid grid-cols-2 gap-2 mb-4">
      <button
        v-for="preset in presetList"
        :key="preset.id"
        @click="setPreset(preset.id)"
        class="preset-card text-left p-3 rounded-lg border transition-all"
        :class="activePresetId === preset.id
          ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)]'
          : 'border-[var(--color-border)] hover:border-[var(--color-border-strong)] bg-[var(--color-surface)]'"
      >
        <div class="flex items-center gap-2 mb-1">
          <span
            class="w-3 h-3 rounded-full shrink-0"
            :style="{ backgroundColor: PRESET_COLORS[preset.id] }"
          />
          <span class="text-sm font-medium text-[var(--color-text)]">{{ preset.name }}</span>
        </div>
        <p class="text-xs text-[var(--color-text-muted)] leading-snug">{{ preset.description }}</p>
      </button>
    </div>

    <!-- Toggle Custom Options -->
    <button
      @click="showCustom = !showCustom"
      class="w-full flex items-center justify-between py-2 px-3 rounded-lg text-sm text-[var(--color-text-secondary)] hover:bg-[var(--color-tint)] transition-colors"
    >
      <span>Customize</span>
      <svg
        class="w-4 h-4 transition-transform"
        :class="showCustom ? 'rotate-180' : ''"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <!-- Custom Options Panel -->
    <div v-if="showCustom" class="mt-3 space-y-4">
      <!-- Primary Color -->
      <div>
        <label class="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">Primary Color</label>
        <div class="flex items-center gap-2">
          <input
            type="color"
            :value="resolvedTheme.primaryColor"
            @input="setCustom('primaryColor', $event.target.value)"
            class="w-8 h-8 rounded cursor-pointer border border-[var(--color-border)] bg-transparent p-0.5"
          />
          <input
            type="text"
            :value="resolvedTheme.primaryColor"
            @change="setCustom('primaryColor', $event.target.value)"
            class="flex-1 px-3 py-1.5 text-xs font-mono border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] focus:outline-none focus:border-[var(--color-primary)]"
            maxlength="7"
          />
        </div>
      </div>

      <!-- Font Family -->
      <div>
        <label class="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">Font Family</label>
        <select
          :value="resolvedTheme.fontFamily"
          @change="setCustom('fontFamily', $event.target.value)"
          class="w-full px-3 py-1.5 text-sm border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] focus:outline-none focus:border-[var(--color-primary)]"
        >
          <option v-for="opt in FONT_OPTIONS" :key="opt.label" :value="opt.value">{{ opt.label }}</option>
        </select>
      </div>

      <!-- Font Size -->
      <div>
        <label class="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">Font Size</label>
        <div class="flex gap-1.5">
          <button
            v-for="opt in SIZE_OPTIONS"
            :key="opt.label"
            @click="selectSize(opt)"
            class="flex-1 py-1.5 text-xs font-medium rounded-lg border transition-colors"
            :class="currentSizeLabel === opt.label
              ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)] text-[var(--color-primary)]'
              : 'border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-border-strong)]'"
          >
            {{ opt.label }}
          </button>
        </div>
      </div>

      <!-- Header Text -->
      <div>
        <label class="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">Header Text</label>
        <input
          type="text"
          :value="resolvedTheme.headerText"
          @input="setCustom('headerText', $event.target.value)"
          placeholder="Optional header for each page"
          class="w-full px-3 py-1.5 text-sm border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-primary)]"
        />
      </div>

      <!-- Footer Text -->
      <div>
        <label class="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">Footer Text</label>
        <input
          type="text"
          :value="resolvedTheme.footerText"
          @input="setCustom('footerText', $event.target.value)"
          placeholder="Optional footer text"
          class="w-full px-3 py-1.5 text-sm border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-primary)]"
        />
      </div>

      <!-- Logo URL -->
      <div>
        <label class="block text-xs font-medium text-[var(--color-text-secondary)] mb-1.5">Logo URL</label>
        <input
          type="text"
          :value="resolvedTheme.logo"
          @input="setCustom('logo', $event.target.value)"
          placeholder="https://example.com/logo.png"
          class="w-full px-3 py-1.5 text-sm border border-[var(--color-border)] rounded-lg bg-[var(--color-surface)] text-[var(--color-text)] placeholder:text-[var(--color-text-muted)] focus:outline-none focus:border-[var(--color-primary)]"
        />
        <div v-if="resolvedTheme.logo" class="mt-2 flex items-center gap-2">
          <img
            :src="resolvedTheme.logo"
            alt="Logo preview"
            class="h-6 max-w-[120px] object-contain"
            @error="$event.target.style.display = 'none'"
          />
          <button
            @click="setCustom('logo', '')"
            class="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-error)]"
          >Remove</button>
        </div>
      </div>
    </div>
  </div>
</template>
