<script setup>
import { ref, onMounted } from 'vue'
import { useUsersStore } from '../../stores/users'
import { useToast } from '../../composables/useToast'

const store = useUsersStore()
const toast = useToast()

const showInviteForm = ref(false)
const inviteEmail = ref('')
const inviteName = ref('')
const inviteRole = ref('viewer')
const inviting = ref(false)

const confirmAction = ref(null)

function formatDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
}

function roleBadgeClass(role) {
  return {
    admin: 'bg-[rgba(32,104,255,0.1)] text-[var(--color-primary)]',
    editor: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
    viewer: 'bg-[rgba(255,86,0,0.1)] text-[var(--color-fin-orange)]',
    guest: 'bg-black/5 text-[var(--color-text-secondary)] dark:bg-white/10',
  }[role] || 'bg-black/5 text-[var(--color-text-secondary)]'
}

function promptRoleChange(user, newRole) {
  if (user.role === newRole) return
  confirmAction.value = {
    type: 'role',
    user,
    newRole,
    message: `Change ${user.name} from ${user.role} to ${newRole}?`,
  }
}

function promptRemove(user) {
  confirmAction.value = {
    type: 'remove',
    user,
    message: `Remove ${user.name}'s access? They can re-login but will get guest role.`,
  }
}

async function executeConfirm() {
  const action = confirmAction.value
  if (!action) return

  if (action.type === 'role') {
    const result = await store.updateRole(action.user.email, action.newRole)
    if (result.success) {
      toast.success(`Updated ${action.user.name} to ${action.newRole}`)
    } else {
      toast.error(result.error)
    }
  } else if (action.type === 'remove') {
    const result = await store.removeUser(action.user.email)
    if (result.success) {
      toast.success(`Removed ${action.user.name}`)
    } else {
      toast.error(result.error)
    }
  }
  confirmAction.value = null
}

async function handleInvite() {
  const email = inviteEmail.value.trim()
  if (!email || !email.includes('@')) {
    toast.error('Enter a valid email address')
    return
  }
  inviting.value = true
  const result = await store.inviteUser(email, inviteName.value.trim(), inviteRole.value)
  inviting.value = false

  if (result.success) {
    toast.success(`Invited ${email}`)
    inviteEmail.value = ''
    inviteName.value = ''
    inviteRole.value = 'viewer'
    showInviteForm.value = false
  } else {
    toast.error(result.error)
  }
}

onMounted(() => {
  store.fetchUsers()
  store.fetchRoles()
})
</script>

<template>
  <section>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-sm font-semibold text-[var(--color-text)]">User Management</h2>
      <button
        @click="showInviteForm = !showInviteForm"
        class="text-xs font-medium px-3 py-1.5 rounded-lg border border-[var(--color-primary)] text-[var(--color-primary)] hover:bg-[var(--color-primary-light)] transition-colors cursor-pointer"
      >
        {{ showInviteForm ? 'Cancel' : 'Invite User' }}
      </button>
    </div>

    <!-- Invite Form -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 -translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-2"
    >
      <div v-if="showInviteForm" class="mb-4 p-4 rounded-lg border border-[var(--color-border)] bg-[var(--color-surface)]">
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div>
            <label class="block text-xs text-[var(--color-text-muted)] mb-1">Email</label>
            <input
              v-model="inviteEmail"
              type="email"
              placeholder="user@company.com"
              class="w-full border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--color-primary)] transition-colors"
            />
          </div>
          <div>
            <label class="block text-xs text-[var(--color-text-muted)] mb-1">Name</label>
            <input
              v-model="inviteName"
              type="text"
              placeholder="Optional"
              class="w-full border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--color-primary)] transition-colors"
            />
          </div>
          <div>
            <label class="block text-xs text-[var(--color-text-muted)] mb-1">Role</label>
            <select
              v-model="inviteRole"
              class="w-full border border-[var(--color-border)] bg-[var(--color-surface)] text-[var(--color-text)] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[var(--color-primary)] focus:ring-1 focus:ring-[var(--color-primary)] transition-colors"
            >
              <option v-for="r in store.roles" :key="r.id" :value="r.id">{{ r.label }}</option>
            </select>
          </div>
        </div>
        <button
          @click="handleInvite"
          :disabled="inviting || !inviteEmail.trim()"
          class="mt-3 text-xs font-semibold px-4 py-2 rounded-lg bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ inviting ? 'Inviting…' : 'Send Invite' }}
        </button>
      </div>
    </Transition>

    <!-- Loading -->
    <div v-if="store.loading" class="text-sm text-[var(--color-text-muted)] py-8 text-center">
      Loading users…
    </div>

    <!-- Users Table -->
    <div v-else class="border border-[var(--color-border)] rounded-lg overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="bg-black/[0.03] dark:bg-white/[0.03]">
              <th class="text-left text-xs font-semibold text-[var(--color-text-muted)] px-4 py-2.5">User</th>
              <th class="text-left text-xs font-semibold text-[var(--color-text-muted)] px-4 py-2.5">Role</th>
              <th class="text-left text-xs font-semibold text-[var(--color-text-muted)] px-4 py-2.5 hidden sm:table-cell">Last Active</th>
              <th class="text-right text-xs font-semibold text-[var(--color-text-muted)] px-4 py-2.5">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="user in store.users"
              :key="user.email"
              class="border-t border-[var(--color-border)]"
            >
              <td class="px-4 py-3">
                <div class="font-medium text-[var(--color-text)]">{{ user.name }}</div>
                <div class="text-xs text-[var(--color-text-muted)]">{{ user.email }}</div>
              </td>
              <td class="px-4 py-3">
                <select
                  :value="user.role"
                  @change="promptRoleChange(user, $event.target.value)"
                  class="text-xs font-semibold px-2.5 py-1 rounded-full border-none cursor-pointer focus:outline-none focus:ring-1 focus:ring-[var(--color-primary)]"
                  :class="roleBadgeClass(user.role)"
                >
                  <option v-for="r in store.roles" :key="r.id" :value="r.id">{{ r.label }}</option>
                </select>
              </td>
              <td class="px-4 py-3 text-[var(--color-text-secondary)] hidden sm:table-cell">
                {{ formatDate(user.last_active) }}
              </td>
              <td class="px-4 py-3 text-right">
                <button
                  @click="promptRemove(user)"
                  class="text-xs text-red-500 hover:text-red-700 transition-colors cursor-pointer"
                >
                  Remove
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="!store.users.length" class="text-sm text-[var(--color-text-muted)] py-8 text-center">
        No users found
      </div>
    </div>

    <!-- Confirmation Dialog -->
    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-100 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div v-if="confirmAction" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="confirmAction = null">
        <div class="bg-[var(--color-surface)] rounded-xl shadow-lg p-6 mx-4 max-w-sm w-full border border-[var(--color-border)]">
          <p class="text-sm text-[var(--color-text)] mb-4">{{ confirmAction.message }}</p>
          <div class="flex justify-end gap-2">
            <button
              @click="confirmAction = null"
              class="text-xs font-medium px-4 py-2 rounded-lg border border-[var(--color-border)] text-[var(--color-text-secondary)] hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              @click="executeConfirm"
              class="text-xs font-semibold px-4 py-2 rounded-lg transition-colors cursor-pointer"
              :class="confirmAction.type === 'remove'
                ? 'bg-red-500 hover:bg-red-600 text-white'
                : 'bg-[var(--color-primary)] hover:bg-[var(--color-primary-hover)] text-white'"
            >
              {{ confirmAction.type === 'remove' ? 'Remove' : 'Confirm' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </section>
</template>
