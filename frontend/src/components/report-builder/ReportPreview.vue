<script setup>
import { ref, computed } from 'vue'
import { marked } from 'marked'
import { API_BASE } from '../../api/client'
import { useToast } from '../../composables/useToast'

const props = defineProps({
  sections: { type: Array, required: true },
  reportId: { type: String, default: null },
})

const { success: toastSuccess, error: toastError } = useToast()

const isFullscreen = ref(false)
const exportMenuOpen = ref(false)
const previewRef = ref(null)

// Build full markdown from sections
const fullMarkdown = computed(() =>
  props.sections.map((s) => (s.content || s).trim()).join('\n\n---\n\n')
)

// Parse all sections into a single HTML block
const fullHtml = computed(() => marked.parse(fullMarkdown.value))

// Generate table of contents from ## headings
const tocEntries = computed(() => {
  const entries = []
  for (const section of props.sections) {
    const content = section.content || section
    const headings = content.matchAll(/^(#{1,3})\s+(.+)/gm)
    for (const match of headings) {
      const level = match[1].length
      const text = match[2].trim()
      const id = text
        .toLowerCase()
        .replace(/[^a-z0-9\s-]/g, '')
        .replace(/\s+/g, '-')
      entries.push({ level, text, id })
    }
  }
  return entries
})

// Estimated page count (~3000 chars per A4 page)
const estimatedPages = computed(() => Math.max(1, Math.ceil(fullMarkdown.value.length / 3000)))

// Configure marked to add IDs to headings for TOC anchor links
const renderer = new marked.Renderer()
const originalHeading = renderer.heading
renderer.heading = function ({ text, depth }) {
  const id = text
    .toLowerCase()
    .replace(/<[^>]*>/g, '')
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
  return `<h${depth} id="${id}">${text}</h${depth}>`
}
marked.use({ renderer })

// Re-render HTML after setting up renderer
const renderedHtml = computed(() => marked.parse(fullMarkdown.value))

function scrollToHeading(id) {
  const container = previewRef.value
  if (!container) return
  const el = container.querySelector(`#${CSS.escape(id)}`)
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

function toggleFullscreen() {
  isFullscreen.value = !isFullscreen.value
}

// --- Export actions ---

async function copyToClipboard() {
  try {
    await navigator.clipboard.writeText(fullMarkdown.value)
    toastSuccess('Report copied to clipboard')
  } catch {
    toastError('Failed to copy to clipboard')
  }
  exportMenuOpen.value = false
}

function downloadFormat(format) {
  if (!props.reportId) return
  window.open(`${API_BASE}/report/${props.reportId}/export?format=${format}`, '_blank')
  exportMenuOpen.value = false
}

function printReport() {
  window.print()
  exportMenuOpen.value = false
}

// Close export menu on outside click
function onExportMenuBlur() {
  setTimeout(() => {
    exportMenuOpen.value = false
  }, 150)
}
</script>

<template>
  <Teleport to="body">
    <Transition name="preview-fullscreen">
      <div
        v-if="isFullscreen"
        class="fixed inset-0 z-50 bg-white overflow-auto print:static print:overflow-visible"
      >
        <!-- Fullscreen toolbar -->
        <div class="sticky top-0 z-10 bg-white/95 backdrop-blur border-b border-[var(--color-border)] px-6 py-3 flex items-center justify-between print:hidden">
          <div class="flex items-center gap-3">
            <span class="text-sm font-semibold text-[var(--color-text)]">Report Preview</span>
            <span class="text-xs text-[var(--color-text-muted)]">{{ estimatedPages }} page{{ estimatedPages !== 1 ? 's' : '' }}</span>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="copyToClipboard"
              class="text-sm px-3 py-1.5 rounded-md border border-[var(--color-border)] hover:bg-[var(--color-tint)] text-[var(--color-text-secondary)] transition-colors"
            >
              Copy
            </button>
            <button
              @click="printReport"
              class="text-sm px-3 py-1.5 rounded-md border border-[var(--color-border)] hover:bg-[var(--color-tint)] text-[var(--color-text-secondary)] transition-colors"
            >
              Print
            </button>
            <button
              @click="toggleFullscreen"
              class="text-sm px-3 py-1.5 rounded-md bg-[var(--color-tint)] hover:bg-[var(--color-border)] text-[var(--color-text)] transition-colors font-medium"
            >
              Exit Preview
            </button>
          </div>
        </div>

        <!-- Fullscreen content with TOC sidebar -->
        <div class="max-w-6xl mx-auto px-6 py-8 grid grid-cols-[220px_1fr] gap-8">
          <!-- TOC sidebar -->
          <nav class="sticky top-20 self-start max-h-[calc(100vh-6rem)] overflow-y-auto print:hidden">
            <h4 class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">Contents</h4>
            <ul class="space-y-1">
              <li
                v-for="entry in tocEntries"
                :key="entry.id"
                :style="{ paddingLeft: `${(entry.level - 1) * 12}px` }"
              >
                <button
                  @click="scrollToHeading(entry.id)"
                  class="text-left text-sm text-[var(--color-text-secondary)] hover:text-[#2068FF] transition-colors truncate block w-full py-0.5"
                >
                  {{ entry.text }}
                </button>
              </li>
            </ul>
          </nav>

          <!-- Rendered content -->
          <div ref="previewRef" class="report-preview-content" v-html="renderedHtml" />
        </div>
      </div>
    </Transition>
  </Teleport>

  <!-- Inline toolbar (always visible in normal mode) -->
  <div class="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg">
    <!-- Toolbar -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-[var(--color-border)]">
      <div class="flex items-center gap-3">
        <h3 class="text-sm font-semibold text-[var(--color-text)]">Preview</h3>
        <span class="text-xs text-[var(--color-text-muted)]">
          {{ tocEntries.length }} section{{ tocEntries.length !== 1 ? 's' : '' }}
          &middot;
          ~{{ estimatedPages }} page{{ estimatedPages !== 1 ? 's' : '' }}
        </span>
      </div>

      <div class="flex items-center gap-2">
        <!-- Copy -->
        <button
          @click="copyToClipboard"
          class="text-xs px-2.5 py-1.5 rounded-md border border-[var(--color-border)] hover:bg-[var(--color-tint)] text-[var(--color-text-secondary)] transition-colors flex items-center gap-1.5"
          title="Copy Markdown to clipboard"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          Copy
        </button>

        <!-- Export dropdown -->
        <div class="relative">
          <button
            @click="exportMenuOpen = !exportMenuOpen"
            @blur="onExportMenuBlur"
            class="text-xs px-2.5 py-1.5 rounded-md border border-[var(--color-border)] hover:bg-[var(--color-tint)] text-[var(--color-text-secondary)] transition-colors flex items-center gap-1.5"
            title="Download report"
          >
            <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
            Export
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          <Transition name="dropdown">
            <div
              v-if="exportMenuOpen"
              class="absolute right-0 mt-1 w-44 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg shadow-lg py-1 z-20"
            >
              <button
                @mousedown.prevent="downloadFormat('markdown')"
                class="w-full text-left px-3 py-2 text-sm text-[var(--color-text-secondary)] hover:bg-[var(--color-tint)] hover:text-[var(--color-text)] transition-colors"
              >
                Markdown (.md)
              </button>
              <button
                @mousedown.prevent="downloadFormat('html')"
                class="w-full text-left px-3 py-2 text-sm text-[var(--color-text-secondary)] hover:bg-[var(--color-tint)] hover:text-[var(--color-text)] transition-colors"
              >
                HTML (.html)
              </button>
              <button
                @mousedown.prevent="downloadFormat('csv')"
                class="w-full text-left px-3 py-2 text-sm text-[var(--color-text-secondary)] hover:bg-[var(--color-tint)] hover:text-[var(--color-text)] transition-colors"
              >
                CSV (.csv)
              </button>
              <div class="border-t border-[var(--color-border)] my-1" />
              <button
                @mousedown.prevent="printReport"
                class="w-full text-left px-3 py-2 text-sm text-[var(--color-text-secondary)] hover:bg-[var(--color-tint)] hover:text-[var(--color-text)] transition-colors"
              >
                Print
              </button>
            </div>
          </Transition>
        </div>

        <!-- Fullscreen toggle -->
        <button
          @click="toggleFullscreen"
          class="text-xs px-2.5 py-1.5 rounded-md bg-[#2068FF] hover:bg-[#1a5ae0] text-white transition-colors flex items-center gap-1.5 font-medium"
          title="Full-screen preview"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
          </svg>
          Preview
        </button>
      </div>
    </div>

    <!-- Inline TOC -->
    <div v-if="tocEntries.length > 0" class="px-4 py-3 border-b border-[var(--color-border)] bg-[var(--color-tint)]/30">
      <h4 class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Table of Contents</h4>
      <div class="flex flex-wrap gap-x-4 gap-y-1">
        <span
          v-for="entry in tocEntries.filter(e => e.level <= 2)"
          :key="entry.id"
          class="text-xs text-[var(--color-text-secondary)] hover:text-[#2068FF] cursor-pointer transition-colors"
          :class="entry.level === 1 ? 'font-semibold' : ''"
          @click="scrollToHeading(entry.id)"
        >
          {{ entry.text }}
        </span>
      </div>
    </div>

    <!-- Preview content (compact inline version) -->
    <div ref="previewRef" class="report-preview-content px-4 md:px-8 py-6 max-h-[500px] overflow-y-auto" v-html="renderedHtml" />
  </div>
</template>

<style scoped>
/* Report content typography — mirrors ReportView styles */
.report-preview-content :deep(h1) { font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem; color: var(--color-text); }
.report-preview-content :deep(h2) { font-size: 1.25rem; font-weight: 600; margin-top: 2rem; margin-bottom: 0.75rem; color: var(--color-text); }
.report-preview-content :deep(h3) { font-size: 1.125rem; font-weight: 600; margin-top: 1.5rem; margin-bottom: 0.5rem; color: var(--color-text); }
.report-preview-content :deep(p) { margin-bottom: 0.75rem; line-height: 1.625; color: var(--color-text-secondary); font-size: 0.875rem; }
.report-preview-content :deep(ul),
.report-preview-content :deep(ol) { margin-bottom: 0.75rem; padding-left: 1.5rem; }
.report-preview-content :deep(li) { margin-bottom: 0.25rem; line-height: 1.625; color: var(--color-text-secondary); font-size: 0.875rem; }
.report-preview-content :deep(ul) { list-style-type: disc; }
.report-preview-content :deep(ol) { list-style-type: decimal; }
.report-preview-content :deep(strong) { font-weight: 600; color: var(--color-text); }
.report-preview-content :deep(blockquote) {
  border-left: 3px solid #2068FF;
  padding-left: 1rem;
  margin: 1rem 0;
  color: var(--color-text-secondary);
  font-style: italic;
}
.report-preview-content :deep(code) {
  background: var(--color-tint);
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.8125rem;
}
.report-preview-content :deep(pre) {
  background: #1a1a2e;
  color: #e0e0e0;
  padding: 1rem;
  border-radius: 0.5rem;
  overflow-x: auto;
  margin: 1rem 0;
}
.report-preview-content :deep(pre code) { background: none; padding: 0; }
.report-preview-content :deep(table) { width: 100%; border-collapse: collapse; margin: 1rem 0; font-size: 0.875rem; }
.report-preview-content :deep(th) {
  text-align: left;
  padding: 0.5rem;
  border-bottom: 2px solid #2068FF;
  font-weight: 600;
  color: var(--color-text);
}
.report-preview-content :deep(td) { padding: 0.5rem; border-bottom: 1px solid var(--color-border); color: var(--color-text-secondary); }
.report-preview-content :deep(hr) { border: none; border-top: 1px solid var(--color-border); margin: 1.5rem 0; }

/* Fullscreen transition */
.preview-fullscreen-enter-active,
.preview-fullscreen-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.preview-fullscreen-enter-from,
.preview-fullscreen-leave-to {
  opacity: 0;
  transform: scale(0.98);
}

/* Dropdown transition */
.dropdown-enter-active,
.dropdown-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}
.dropdown-enter-from,
.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
