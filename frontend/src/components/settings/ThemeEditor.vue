<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useThemeStore } from '../../stores/themes'
import { useToast } from '../../composables/useToast'

const store = useThemeStore()
const toast = useToast()

const editingId = ref(null)
const themeName = ref('')
const showImportModal = ref(false)
const importJson = ref('')

const draft = reactive({ ...store.DEFAULT_THEME_PROPS })

const radiusValue = computed({
  get: () => parseFloat(draft['--radius']) || 0.5,
  set: (v) => {
    draft['--radius-sm'] = `${(v * 0.75).toFixed(3)}rem`
    draft['--radius'] = `${v.toFixed(3)}rem`
    draft['--radius-lg'] = `${(v * 1.5).toFixed(3)}rem`
    draft['--radius-xl'] = `${(v * 2).toFixed(3)}rem`
  },
})

const shadowIntensity = computed({
  get: () => parseFloat(draft['--shadow-intensity']) || 1,
  set: (v) => { draft['--shadow-intensity'] = String(v) },
})

const colorFields = [
  { key: '--color-primary', label: 'Primary' },
  { key: '--color-accent', label: 'Accent' },
  { key: '--color-fin-orange', label: 'Orange' },
  { key: '--color-bg', label: 'Background' },
  { key: '--color-surface', label: 'Surface' },
  { key: '--color-text', label: 'Text' },
  { key: '--color-text-secondary', label: 'Text Secondary' },
]

function resetDraft() {
  Object.assign(draft, store.DEFAULT_THEME_PROPS)
  editingId.value = null
  themeName.value = ''
}

function editTheme(theme) {
  editingId.value = theme.id
  themeName.value = theme.name
  Object.assign(draft, store.DEFAULT_THEME_PROPS, theme.props)
}

function saveCurrentTheme() {
  const name = themeName.value.trim()
  if (!name) {
    toast.error('Please enter a theme name')
    return
  }
  const props = { ...draft }
  if (editingId.value) {
    store.updateTheme(editingId.value, name, props)
    toast.success(`Theme "${name}" updated`)
  } else {
    const id = store.saveTheme(name, props)
    editingId.value = id
    toast.success(`Theme "${name}" saved`)
  }
}

function deleteTheme(id) {
  store.deleteTheme(id)
  if (editingId.value === id) resetDraft()
  toast.success('Theme deleted')
}

function handleExport(id) {
  const json = store.exportTheme(id)
  if (!json) return
  navigator.clipboard.writeText(json).then(() => {
    toast.success('Theme JSON copied to clipboard')
  }).catch(() => {
    // Fallback: open in prompt
    const el = document.createElement('textarea')
    el.value = json
    document.body.appendChild(el)
    el.select()
    document.execCommand('copy')
    document.body.removeChild(el)
    toast.success('Theme JSON copied')
  })
}

function handleImport() {
  try {
    const id = store.importTheme(importJson.value)
    showImportModal.value = false
    importJson.value = ''
    const theme = store.themes.find((t) => t.id === id)
    if (theme) editTheme(theme)
    toast.success('Theme imported')
  } catch {
    toast.error('Invalid theme JSON')
  }
}

// Preview styles computed from draft
const previewStyles = computed(() => {
  const intensity = parseFloat(draft['--shadow-intensity'] || 1)
  return {
    '--p-primary': draft['--color-primary'],
    '--p-accent': draft['--color-accent'],
    '--p-orange': draft['--color-fin-orange'],
    '--p-bg': draft['--color-bg'],
    '--p-surface': draft['--color-surface'],
    '--p-text': draft['--color-text'],
    '--p-text-sec': draft['--color-text-secondary'],
    '--p-font': draft['--font-family'],
    '--p-radius': draft['--radius'],
    '--p-radius-lg': draft['--radius-lg'],
    '--p-shadow': `0 1px 3px rgba(0,0,0,${(0.1 * intensity).toFixed(3)})`,
    '--p-shadow-md': `0 4px 6px rgba(0,0,0,${(0.07 * intensity).toFixed(3)})`,
  }
})
</script>

<template>
  <div class="space-y-6">
    <!-- Saved themes list -->
    <div v-if="store.themes.length" class="space-y-2">
      <h3 class="text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">Custom Themes</h3>
      <div
        v-for="theme in store.themes"
        :key="theme.id"
        class="flex items-center gap-3 p-3 rounded-lg border transition-colors"
        :class="store.activeThemeId === theme.id
          ? 'border-[var(--color-primary)] bg-[var(--color-primary-light)]'
          : 'border-[var(--color-border)] hover:border-[var(--color-primary)]/50'"
      >
        <!-- Color swatches -->
        <div class="flex -space-x-1 shrink-0">
          <span
            v-for="key in ['--color-primary', '--color-accent', '--color-fin-orange']"
            :key="key"
            class="w-5 h-5 rounded-full border border-white"
            :style="{ backgroundColor: theme.props[key] || store.DEFAULT_THEME_PROPS[key] }"
          />
        </div>

        <span class="text-sm font-medium text-[var(--color-text)] flex-1 truncate">{{ theme.name }}</span>

        <div class="flex gap-1 shrink-0">
          <button
            @click="store.activateTheme(theme.id)"
            class="px-2 py-1 text-xs rounded border transition-colors cursor-pointer"
            :class="store.activeThemeId === theme.id
              ? 'bg-[var(--color-primary)] text-white border-[var(--color-primary)]'
              : 'border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-primary)]'"
          >
            {{ store.activeThemeId === theme.id ? 'Active' : 'Apply' }}
          </button>
          <button
            @click="editTheme(theme)"
            class="px-2 py-1 text-xs rounded border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-primary)] transition-colors cursor-pointer"
          >Edit</button>
          <button
            @click="handleExport(theme.id)"
            class="px-2 py-1 text-xs rounded border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[var(--color-primary)] transition-colors cursor-pointer"
            title="Copy as JSON"
          >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </button>
          <button
            @click="deleteTheme(theme.id)"
            class="px-2 py-1 text-xs rounded border border-[var(--color-border)] text-[var(--color-error)] hover:border-[var(--color-error)] transition-colors cursor-pointer"
            title="Delete"
          >
            <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Deactivate button -->
      <button
        v-if="store.activeThemeId"
        @click="store.deactivateTheme()"
        class="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors cursor-pointer"
      >
        Reset to default theme
      </button>
    </div>

    <!-- Editor panel -->
    <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg p-4 md:p-5 space-y-5">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-semibold text-[var(--color-text)]">
          {{ editingId ? 'Edit Theme' : 'Create Theme' }}
        </h3>
        <div class="flex gap-2">
          <button
            @click="showImportModal = true"
            class="text-xs text-[var(--color-primary)] hover:underline cursor-pointer"
          >Import JSON</button>
          <button
            @click="resetDraft"
            class="text-xs text-[var(--color-text-muted)] hover:text-[var(--color-text)] cursor-pointer"
          >Reset</button>
        </div>
      </div>

      <!-- Theme name -->
      <div>
        <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-1.5">Theme Name</label>
        <input
          v-model="themeName"
          type="text"
          placeholder="My Custom Theme"
          class="w-full border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[var(--color-primary)] focus:outline-none transition-colors"
        />
      </div>

      <!-- Colors -->
      <div>
        <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">Colors</label>
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          <div v-for="field in colorFields" :key="field.key" class="flex items-center gap-2">
            <label
              class="relative w-8 h-8 rounded-lg border border-[var(--color-border)] overflow-hidden cursor-pointer shrink-0"
              :style="{ backgroundColor: draft[field.key] }"
            >
              <input
                type="color"
                :value="draft[field.key]"
                @input="draft[field.key] = $event.target.value"
                class="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
              />
            </label>
            <div class="min-w-0">
              <div class="text-xs font-medium text-[var(--color-text)] truncate">{{ field.label }}</div>
              <div class="text-[10px] text-[var(--color-text-muted)] font-mono">{{ draft[field.key] }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Font family -->
      <div>
        <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">Body Font</label>
        <select
          :value="draft['--font-family']"
          @change="draft['--font-family'] = $event.target.value"
          class="w-full border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[var(--color-primary)] focus:outline-none"
        >
          <option
            v-for="font in store.FONT_OPTIONS"
            :key="font.value"
            :value="font.value"
            :style="{ fontFamily: font.value }"
          >{{ font.label }}</option>
        </select>
      </div>

      <!-- Border radius slider -->
      <div>
        <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">
          Border Radius — {{ radiusValue.toFixed(2) }}rem
        </label>
        <input
          type="range"
          :value="radiusValue"
          @input="radiusValue = parseFloat($event.target.value)"
          min="0"
          max="1.5"
          step="0.05"
          class="w-full accent-[var(--color-primary)]"
        />
        <div class="flex justify-between text-[10px] text-[var(--color-text-muted)]">
          <span>Sharp</span>
          <span>Rounded</span>
        </div>
      </div>

      <!-- Shadow intensity slider -->
      <div>
        <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">
          Shadow Intensity — {{ (shadowIntensity * 100).toFixed(0) }}%
        </label>
        <input
          type="range"
          :value="shadowIntensity"
          @input="shadowIntensity = parseFloat($event.target.value)"
          min="0"
          max="3"
          step="0.1"
          class="w-full accent-[var(--color-primary)]"
        />
        <div class="flex justify-between text-[10px] text-[var(--color-text-muted)]">
          <span>None</span>
          <span>Heavy</span>
        </div>
      </div>

      <!-- Live preview -->
      <div>
        <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-2">Preview</label>
        <div
          class="border border-[var(--color-border)] rounded-lg overflow-hidden"
          :style="previewStyles"
        >
          <div
            class="p-4 space-y-3"
            :style="{
              backgroundColor: 'var(--p-bg)',
              fontFamily: 'var(--p-font)',
              color: 'var(--p-text)',
            }"
          >
            <!-- Mini nav bar -->
            <div
              class="flex items-center justify-between p-2 px-3"
              :style="{
                backgroundColor: 'var(--p-surface)',
                borderRadius: 'var(--p-radius-lg)',
                boxShadow: 'var(--p-shadow)',
              }"
            >
              <span class="text-xs font-bold" :style="{ color: 'var(--p-primary)' }">MiroFish</span>
              <div class="flex gap-2">
                <span class="text-[10px]" :style="{ color: 'var(--p-text-sec)' }">Dashboard</span>
                <span class="text-[10px]" :style="{ color: 'var(--p-text-sec)' }">Reports</span>
              </div>
            </div>

            <!-- Mini cards -->
            <div class="grid grid-cols-3 gap-2">
              <div
                v-for="(item, i) in [
                  { label: 'Agents', value: '200', color: 'var(--p-primary)' },
                  { label: 'Sentiment', value: '+72%', color: 'var(--p-accent)' },
                  { label: 'Mentions', value: '1.4k', color: 'var(--p-orange)' },
                ]"
                :key="i"
                class="p-2"
                :style="{
                  backgroundColor: 'var(--p-surface)',
                  borderRadius: 'var(--p-radius)',
                  boxShadow: 'var(--p-shadow)',
                }"
              >
                <div class="text-[10px]" :style="{ color: 'var(--p-text-sec)' }">{{ item.label }}</div>
                <div class="text-sm font-bold" :style="{ color: item.color }">{{ item.value }}</div>
              </div>
            </div>

            <!-- Mini button row -->
            <div class="flex gap-2">
              <span
                class="text-[10px] px-3 py-1 text-white font-medium"
                :style="{
                  backgroundColor: 'var(--p-primary)',
                  borderRadius: 'var(--p-radius)',
                }"
              >Run Simulation</span>
              <span
                class="text-[10px] px-3 py-1 font-medium border"
                :style="{
                  borderColor: 'var(--p-primary)',
                  color: 'var(--p-primary)',
                  borderRadius: 'var(--p-radius)',
                }"
              >View Report</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Save / Update -->
      <div class="flex gap-2">
        <button
          @click="saveCurrentTheme"
          class="flex-1 bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white text-sm font-semibold px-4 py-2.5 rounded-lg transition-colors cursor-pointer"
        >
          {{ editingId ? 'Update Theme' : 'Save Theme' }}
        </button>
        <button
          v-if="editingId"
          @click="resetDraft"
          class="px-4 py-2.5 text-sm border border-[var(--color-border)] text-[var(--color-text-secondary)] rounded-lg hover:border-[var(--color-primary)] transition-colors cursor-pointer"
        >Cancel</button>
      </div>
    </div>

    <!-- Import modal -->
    <teleport to="body">
      <div
        v-if="showImportModal"
        class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
        @click.self="showImportModal = false"
      >
        <div class="bg-[var(--color-surface)] rounded-xl p-5 w-full max-w-md space-y-4 shadow-lg">
          <h3 class="text-sm font-semibold text-[var(--color-text)]">Import Theme</h3>
          <textarea
            v-model="importJson"
            placeholder='Paste theme JSON here...'
            rows="8"
            class="w-full border border-[var(--color-border)] bg-[var(--color-bg)] text-[var(--color-text)] rounded-lg px-3 py-2 text-xs font-mono focus:ring-2 focus:ring-[var(--color-primary)] focus:outline-none resize-y"
          />
          <div class="flex gap-2 justify-end">
            <button
              @click="showImportModal = false"
              class="px-4 py-2 text-sm border border-[var(--color-border)] text-[var(--color-text-secondary)] rounded-lg cursor-pointer hover:border-[var(--color-primary)] transition-colors"
            >Cancel</button>
            <button
              @click="handleImport"
              :disabled="!importJson.trim()"
              class="px-4 py-2 text-sm bg-[var(--color-primary)] text-white rounded-lg cursor-pointer hover:bg-[var(--color-primary-hover)] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >Import</button>
          </div>
        </div>
      </div>
    </teleport>
  </div>
</template>
