<script setup>
import { computed } from 'vue'

const props = defineProps({
  name: { type: String, default: '' },
  role: { type: String, default: '' },
  company: { type: String, default: '' },
  fullName: { type: String, default: '' },
  sentiment: { type: String, default: '' },
  totalActions: { type: Number, default: 0 },
  twitterActions: { type: Number, default: 0 },
  redditActions: { type: Number, default: 0 },
  compact: { type: Boolean, default: false },
  clickable: { type: Boolean, default: false },
})

defineEmits(['click'])

function hashCode(str) {
  let hash = 0
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash + str.charCodeAt(i)) | 0
  }
  return Math.abs(hash)
}

const parsed = computed(() => {
  if (props.name) {
    return { name: props.name, role: props.role, company: props.company }
  }
  const raw = props.fullName
  const parenMatch = raw.match(/^(.+?)\s*\((.+)\)$/)
  const inner = parenMatch ? parenMatch[2] : ''
  const nameStr = parenMatch ? parenMatch[1].trim() : raw.split(',')[0]?.trim() || raw

  if (inner) {
    const atIdx = inner.indexOf('@')
    return {
      name: nameStr,
      role: atIdx > -1 ? inner.slice(0, atIdx).trim() : inner.trim(),
      company: atIdx > -1 ? inner.slice(atIdx + 1).trim() : '',
    }
  }

  const parts = raw.split(',')
  if (parts.length < 2) return { name: nameStr, role: '', company: '' }
  const afterComma = parts.slice(1).join(',').trim()
  const atIdx = afterComma.indexOf('@')
  return {
    name: nameStr,
    role: atIdx > -1 ? afterComma.slice(0, atIdx).trim() : afterComma,
    company: atIdx > -1 ? afterComma.slice(atIdx + 1).trim() : '',
  }
})

const initial = computed(() => (parsed.value.name || '?')[0].toUpperCase())

const AVATAR_COLORS = [
  '#2068FF', '#ff5600', '#AA00FF', '#009900',
  '#1a5ae0', '#e04500', '#8800cc', '#007700',
]

const avatarColor = computed(() => {
  const idx = hashCode(parsed.value.name) % AVATAR_COLORS.length
  return AVATAR_COLORS[idx]
})

const sentimentConfig = computed(() => {
  const s = (props.sentiment || '').toLowerCase()
  if (s === 'positive' || s === 'engaged')
    return { label: props.sentiment, color: 'var(--color-success)' }
  if (s === 'skeptical')
    return { label: props.sentiment, color: 'var(--color-warning)' }
  if (s === 'cautious')
    return { label: props.sentiment, color: 'var(--color-fin-orange)' }
  if (s === 'moderate')
    return { label: props.sentiment, color: 'var(--color-warning)' }
  if (s === 'negative')
    return { label: props.sentiment, color: 'var(--color-error)' }
  if (props.sentiment)
    return { label: props.sentiment, color: 'var(--color-primary)' }
  return null
})

const hasStats = computed(() => props.totalActions > 0)
</script>

<template>
  <component
    :is="clickable ? 'button' : 'div'"
    :class="[
      'bg-[var(--color-surface)] border border-[var(--color-border)] text-left w-full',
      compact ? 'rounded-lg p-3' : 'rounded-xl p-5',
      clickable && 'cursor-pointer transition-shadow hover:shadow-md hover:border-[var(--color-primary-border)]',
    ]"
    @click="clickable && $emit('click')"
  >
    <div class="flex items-start gap-3">
      <!-- Avatar -->
      <div
        class="shrink-0 rounded-full text-white flex items-center justify-center font-semibold"
        :class="compact ? 'w-9 h-9 text-sm' : 'w-12 h-12 text-lg'"
        :style="{ backgroundColor: avatarColor }"
      >
        {{ initial }}
      </div>

      <!-- Info -->
      <div class="flex-1 min-w-0">
        <div
          class="font-semibold text-[var(--color-text)] truncate"
          :class="compact ? 'text-sm' : 'text-base'"
        >
          {{ parsed.name }}
        </div>
        <p
          v-if="parsed.role || parsed.company"
          class="text-[var(--color-text-muted)] truncate mt-0.5"
          :class="compact ? 'text-[11px]' : 'text-xs'"
        >
          {{ parsed.role }}
          <span v-if="parsed.company">@ {{ parsed.company }}</span>
        </p>

        <!-- Badges row -->
        <div v-if="sentimentConfig || hasStats" class="flex items-center gap-2 mt-2 flex-wrap">
          <span
            v-if="sentimentConfig"
            class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium"
            :style="{
              background: sentimentConfig.color + '15',
              color: sentimentConfig.color,
            }"
          >
            <span
              class="w-1.5 h-1.5 rounded-full"
              :style="{ background: sentimentConfig.color }"
            />
            {{ sentimentConfig.label }}
          </span>
          <span v-if="hasStats && !compact" class="text-[10px] text-[var(--color-text-muted)]">
            {{ totalActions }} actions
          </span>
        </div>
      </div>
    </div>

    <!-- Stats bar (non-compact only) -->
    <div v-if="hasStats && !compact" class="grid grid-cols-3 gap-2 mt-4">
      <div class="bg-[var(--color-tint)] rounded-lg p-2 text-center">
        <div class="text-sm font-semibold text-[var(--color-text)]">{{ totalActions }}</div>
        <div class="text-[10px] text-[var(--color-text-muted)]">Total</div>
      </div>
      <div class="bg-[rgba(32,104,255,0.06)] rounded-lg p-2 text-center">
        <div class="text-sm font-semibold text-[var(--color-primary)]">{{ twitterActions }}</div>
        <div class="text-[10px] text-[var(--color-primary)]">Twitter</div>
      </div>
      <div class="bg-[rgba(255,86,0,0.06)] rounded-lg p-2 text-center">
        <div class="text-sm font-semibold text-[var(--color-fin-orange)]">{{ redditActions }}</div>
        <div class="text-[10px] text-[var(--color-fin-orange)]">Reddit</div>
      </div>
    </div>
  </component>
</template>
