<script setup>
import { ref, computed, watch } from 'vue'
import { reportApi } from '../../api/report'
import { useToast } from '../../composables/useToast'
import AppModal from '../common/AppModal.vue'

const props = defineProps({
  open: Boolean,
  reportId: String,
})

const emit = defineEmits(['close'])

const toast = useToast()

const loading = ref(false)
const shareInfo = ref(null)
const revoking = ref(false)

const shareUrl = computed(() => {
  if (!shareInfo.value?.token) return ''
  return `${window.location.origin}/report/shared/${shareInfo.value.token}`
})

watch(
  () => props.open,
  async (isOpen) => {
    if (isOpen && props.reportId) {
      await fetchOrCreateShare()
    }
  }
)

async function fetchOrCreateShare() {
  loading.value = true
  try {
    // Check if share already exists
    const res = await reportApi.getShare(props.reportId)
    if (res.data?.is_shared && res.data?.data) {
      shareInfo.value = res.data.data
    } else {
      // Create new share link
      const createRes = await reportApi.createShare(props.reportId)
      if (createRes.data?.success) {
        shareInfo.value = createRes.data.data
      }
    }
  } catch {
    toast.error('Failed to generate share link')
  } finally {
    loading.value = false
  }
}

async function copyLink() {
  if (!shareUrl.value) return
  try {
    await navigator.clipboard.writeText(shareUrl.value)
    toast.success('Link copied to clipboard')
  } catch {
    // Fallback for non-secure contexts
    const textarea = document.createElement('textarea')
    textarea.value = shareUrl.value
    textarea.style.position = 'fixed'
    textarea.style.opacity = '0'
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')
    document.body.removeChild(textarea)
    toast.success('Link copied to clipboard')
  }
}

function shareViaEmail() {
  const subject = encodeURIComponent('GTM Simulation Report')
  const body = encodeURIComponent(
    `Check out this GTM simulation report:\n\n${shareUrl.value}`
  )
  window.open(`mailto:?subject=${subject}&body=${body}`, '_self')
}

async function revokeLink() {
  revoking.value = true
  try {
    await reportApi.revokeShare(props.reportId)
    shareInfo.value = null
    toast.info('Share link revoked')
    emit('close')
  } catch {
    toast.error('Failed to revoke share link')
  } finally {
    revoking.value = false
  }
}
</script>

<template>
  <AppModal :open="open" title="Share Report" @close="emit('close')">
    <!-- Loading state -->
    <div v-if="loading" class="flex items-center justify-center py-8">
      <svg class="w-5 h-5 animate-spin text-[#2068FF]" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
      <span class="ml-2 text-sm text-[var(--color-text-muted)]">Generating share link...</span>
    </div>

    <!-- Share content -->
    <div v-else-if="shareInfo" class="space-y-5">
      <p class="text-sm text-[var(--color-text-secondary)]">
        Anyone with this link can view a read-only version of the report.
      </p>

      <!-- Copy link row -->
      <div class="flex gap-2">
        <input
          :value="shareUrl"
          readonly
          class="flex-1 px-3 py-2 bg-[var(--color-tint)] border border-[var(--color-border)] rounded-lg text-sm text-[var(--color-text)] font-mono truncate"
          @focus="$event.target.select()"
        />
        <button
          @click="copyLink"
          class="shrink-0 bg-[#2068FF] hover:bg-[#1a5ae0] text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
          </svg>
          Copy
        </button>
      </div>

      <!-- Share via email -->
      <button
        @click="shareViaEmail"
        class="w-full flex items-center gap-3 px-4 py-3 border border-[var(--color-border)] rounded-lg hover:bg-[var(--color-tint)] transition-colors text-left"
      >
        <svg class="w-5 h-5 text-[var(--color-text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
        <div>
          <div class="text-sm font-medium text-[var(--color-text)]">Share via email</div>
          <div class="text-xs text-[var(--color-text-muted)]">Opens your default email client</div>
        </div>
      </button>

      <!-- Revoke -->
      <div class="pt-2 border-t border-[var(--color-border)]">
        <button
          @click="revokeLink"
          :disabled="revoking"
          class="text-sm text-red-500 hover:text-red-600 disabled:opacity-50 transition-colors"
        >
          {{ revoking ? 'Revoking...' : 'Revoke share link' }}
        </button>
      </div>
    </div>

    <!-- Error / no share fallback -->
    <div v-else class="py-6 text-center text-sm text-[var(--color-text-muted)]">
      Unable to generate share link. Please try again.
    </div>
  </AppModal>
</template>
