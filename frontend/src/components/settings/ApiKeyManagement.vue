<script setup>
import { ref, onMounted } from 'vue'
import { API_BASE } from '../../api/client'
import { useToast } from '../../composables/useToast'
import { useDemoMode } from '../../composables/useDemoMode'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
import AppModal from '../common/AppModal.vue'

const toast = useToast()
const { isDemoMode } = useDemoMode()

const keys = ref([])
const scopes = ref([])
const loading = ref(false)

const newKeyName = ref('')
const newKeyScopes = ref([])
const creating = ref(false)

const createdKey = ref(null)
const showCreatedModal = ref(false)
const copied = ref(false)

const revokeTarget = ref(null)
const showRevokeDialog = ref(false)

async function fetchScopes() {
  try {
    const res = await fetch(`${API_BASE}/v1/api-keys/scopes`)
    const data = await res.json()
    if (data.ok) scopes.value = data.data
  } catch {
    // Scopes will remain empty; form still works
  }
}

async function fetchKeys() {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/v1/api-keys`)
    const data = await res.json()
    if (data.ok) keys.value = data.data
  } catch {
    toast.error('Failed to load API keys')
  } finally {
    loading.value = false
  }
}

async function generateKey() {
  const name = newKeyName.value.trim()
  if (!name) return

  creating.value = true
  try {
    const res = await fetch(`${API_BASE}/v1/api-keys`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, scopes: newKeyScopes.value }),
    })
    const data = await res.json()
    if (data.ok) {
      createdKey.value = data.data
      showCreatedModal.value = true
      newKeyName.value = ''
      newKeyScopes.value = []
      await fetchKeys()
    } else {
      toast.error(data.error || 'Failed to create key')
    }
  } catch {
    toast.error('Network error — is the backend running?')
  } finally {
    creating.value = false
  }
}

function promptRevoke(key) {
  revokeTarget.value = key
  showRevokeDialog.value = true
}

async function confirmRevoke() {
  if (!revokeTarget.value) return
  try {
    const res = await fetch(`${API_BASE}/v1/api-keys/${revokeTarget.value.id}`, {
      method: 'DELETE',
    })
    const data = await res.json()
    if (data.ok) {
      toast.success(`Revoked key "${revokeTarget.value.name}"`)
      await fetchKeys()
    } else {
      toast.error(data.error || 'Failed to revoke key')
    }
  } catch {
    toast.error('Network error')
  }
  revokeTarget.value = null
}

async function copyKey() {
  if (!createdKey.value?.key) return
  try {
    await navigator.clipboard.writeText(createdKey.value.key)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    toast.error('Failed to copy — please select and copy manually')
  }
}

function closeCreatedModal() {
  showCreatedModal.value = false
  createdKey.value = null
  copied.value = false
}

function toggleScope(scopeId) {
  const idx = newKeyScopes.value.indexOf(scopeId)
  if (idx >= 0) {
    newKeyScopes.value.splice(idx, 1)
  } else {
    newKeyScopes.value.push(scopeId)
  }
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}

onMounted(() => {
  fetchScopes()
  fetchKeys()
})
</script>

<template>
  <div>
    <!-- Create New Key -->
    <div class="border border-[var(--color-border)] rounded-lg p-4 mb-6">
      <h3 class="text-sm font-medium text-[var(--color-text)] mb-3">Create New Key</h3>
      <div class="space-y-3">
        <div>
          <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-1.5">Name</label>
          <input
            v-model="newKeyName"
            type="text"
            placeholder="e.g. CI Pipeline, Zapier Integration"
            maxlength="64"
            class="w-full border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-[#2068FF] focus:outline-none"
          />
        </div>

        <div v-if="scopes.length">
          <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-1.5">Permissions</label>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="scope in scopes"
              :key="scope.id"
              @click="toggleScope(scope.id)"
              class="px-3 py-1.5 text-xs rounded-lg border transition-colors cursor-pointer"
              :class="newKeyScopes.includes(scope.id)
                ? 'border-[#2068FF] bg-[rgba(32,104,255,0.08)] text-[#2068FF]'
                : 'border-[var(--color-border)] text-[var(--color-text-secondary)] hover:border-[#2068FF]/50'"
            >
              {{ scope.label }}
            </button>
          </div>
        </div>

        <button
          @click="generateKey"
          :disabled="!newKeyName.trim() || creating"
          class="px-4 py-2 text-sm font-medium rounded-lg bg-[#2068FF] text-white hover:bg-[#1a5ae0] transition-colors disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
        >
          {{ creating ? 'Generating...' : 'Generate Key' }}
        </button>
      </div>
    </div>

    <!-- Existing Keys -->
    <div v-if="loading" class="text-sm text-[var(--color-text-muted)] py-4 text-center">Loading keys...</div>

    <div v-else-if="keys.length === 0" class="text-sm text-[var(--color-text-muted)] py-4 text-center">
      No API keys yet. Create one above to get started.
    </div>

    <div v-else class="space-y-3">
      <div
        v-for="key in keys"
        :key="key.id"
        class="flex flex-col sm:flex-row sm:items-center gap-3 border border-[var(--color-border)] rounded-lg p-4"
      >
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1">
            <span class="text-sm font-medium text-[var(--color-text)] truncate">{{ key.name }}</span>
            <code class="text-xs bg-[var(--color-border)] text-[var(--color-text-muted)] px-1.5 py-0.5 rounded shrink-0">{{ key.prefix }}...</code>
          </div>
          <div class="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-[var(--color-text-muted)]">
            <span>Created {{ formatDate(key.created_at) }}</span>
            <span>Last used {{ key.last_used_at ? formatDate(key.last_used_at) : 'never' }}</span>
          </div>
          <div v-if="key.scopes?.length" class="flex flex-wrap gap-1 mt-2">
            <span
              v-for="scope in key.scopes"
              :key="scope"
              class="px-2 py-0.5 text-[10px] rounded bg-[rgba(32,104,255,0.06)] text-[#2068FF] border border-[#2068FF]/15"
            >{{ scope }}</span>
          </div>
        </div>

        <button
          @click="promptRevoke(key)"
          class="px-3 py-1.5 text-xs font-medium rounded-lg border border-red-200 text-red-600 hover:bg-red-50 dark:border-red-800 dark:text-red-400 dark:hover:bg-red-950 transition-colors cursor-pointer shrink-0"
        >
          Revoke
        </button>
      </div>
    </div>

    <!-- Created Key Modal -->
    <AppModal :open="showCreatedModal" title="API Key Created" @close="closeCreatedModal">
      <div class="space-y-4">
        <div class="bg-[rgba(255,86,0,0.06)] border border-[#ff5600]/20 rounded-lg p-3 text-sm text-[var(--color-text-secondary)]">
          Copy this key now — it won't be shown again.
        </div>

        <div>
          <label class="block text-xs uppercase tracking-wider text-[var(--color-text-muted)] mb-1.5">Key</label>
          <div class="flex gap-2">
            <code class="flex-1 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-lg px-3 py-2 text-sm text-[var(--color-text)] break-all select-all font-mono">{{ createdKey?.key }}</code>
            <button
              @click="copyKey"
              class="px-3 py-2 text-sm border rounded-lg transition-colors shrink-0 cursor-pointer"
              :class="copied
                ? 'border-[var(--color-success)] text-[var(--color-success)]'
                : 'border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-[var(--color-primary-light)]'"
            >
              {{ copied ? '✓ Copied' : 'Copy' }}
            </button>
          </div>
        </div>

        <div class="text-xs text-[var(--color-text-muted)]">
          <strong>Name:</strong> {{ createdKey?.name }}<br />
          <strong>Scopes:</strong> {{ createdKey?.scopes?.join(', ') || 'all' }}
        </div>
      </div>

      <template #footer>
        <div class="flex justify-end">
          <button
            @click="closeCreatedModal"
            class="px-4 py-2 text-sm font-medium rounded-lg bg-[#2068FF] text-white hover:bg-[#1a5ae0] transition-colors cursor-pointer"
          >
            Done
          </button>
        </div>
      </template>
    </AppModal>

    <!-- Revoke Confirmation -->
    <ConfirmDialog
      v-model="showRevokeDialog"
      title="Revoke API Key"
      :message="`Are you sure you want to revoke '${revokeTarget?.name}'? Any integrations using this key will stop working immediately.`"
      confirm-label="Revoke"
      :destructive="true"
      @confirm="confirmRevoke"
    />
  </div>
</template>
