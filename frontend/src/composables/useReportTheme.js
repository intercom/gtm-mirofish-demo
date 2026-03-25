import { ref, computed, watch } from 'vue'

const STORAGE_KEY = 'mirofish-report-theme'

const THEME_PRESETS = {
  intercom: {
    id: 'intercom',
    name: 'Intercom',
    description: 'Brand blue, clean and modern',
    primaryColor: '#2068FF',
    fontFamily: "system-ui, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    headingSize: '1.5rem',
    bodySize: '0.875rem',
    headerText: '',
    footerText: '',
    logo: '',
  },
  corporate: {
    id: 'corporate',
    name: 'Corporate',
    description: 'Dark navy, formal tone',
    primaryColor: '#050505',
    fontFamily: "'Georgia', 'Times New Roman', serif",
    headingSize: '1.625rem',
    bodySize: '0.9375rem',
    headerText: '',
    footerText: '',
    logo: '',
  },
  minimal: {
    id: 'minimal',
    name: 'Minimal',
    description: 'Mostly white, thin lines',
    primaryColor: '#555555',
    fontFamily: "'Helvetica Neue', Helvetica, Arial, sans-serif",
    headingSize: '1.375rem',
    bodySize: '0.875rem',
    headerText: '',
    footerText: '',
    logo: '',
  },
  colorful: {
    id: 'colorful',
    name: 'Colorful',
    description: 'Vibrant, modern palette',
    primaryColor: '#ff5600',
    fontFamily: "system-ui, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    headingSize: '1.5rem',
    bodySize: '0.875rem',
    headerText: '',
    footerText: '',
    logo: '',
  },
}

const activePresetId = ref('intercom')
const customOverrides = ref({})

let initialized = false

function loadFromStorage() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const parsed = JSON.parse(saved)
      if (parsed.presetId && THEME_PRESETS[parsed.presetId]) {
        activePresetId.value = parsed.presetId
      }
      if (parsed.overrides && typeof parsed.overrides === 'object') {
        customOverrides.value = parsed.overrides
      }
    }
  } catch {
    // Corrupted data — use defaults
  }
}

function saveToStorage() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({
    presetId: activePresetId.value,
    overrides: customOverrides.value,
  }))
}

export function useReportTheme() {
  if (!initialized) {
    initialized = true
    loadFromStorage()
    watch([activePresetId, customOverrides], saveToStorage, { deep: true, flush: 'post' })
  }

  const activePreset = computed(() => THEME_PRESETS[activePresetId.value] || THEME_PRESETS.intercom)

  const resolvedTheme = computed(() => ({
    ...activePreset.value,
    ...customOverrides.value,
  }))

  const themeStyles = computed(() => ({
    '--report-primary': resolvedTheme.value.primaryColor,
    '--report-font-family': resolvedTheme.value.fontFamily,
    '--report-heading-size': resolvedTheme.value.headingSize,
    '--report-body-size': resolvedTheme.value.bodySize,
  }))

  function setPreset(presetId) {
    if (!THEME_PRESETS[presetId]) return
    activePresetId.value = presetId
    customOverrides.value = {}
  }

  function setCustom(key, value) {
    customOverrides.value = { ...customOverrides.value, [key]: value }
  }

  function resetCustom() {
    customOverrides.value = {}
  }

  return {
    presets: THEME_PRESETS,
    activePresetId,
    activePreset,
    resolvedTheme,
    themeStyles,
    setPreset,
    setCustom,
    resetCustom,
  }
}
