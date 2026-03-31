import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { usersApi } from '../api/users'

const DEMO_USERS = [
  { email: 'admin@intercom.io', name: 'Alice Chen', role: 'admin', last_active: new Date().toISOString() },
  { email: 'editor@intercom.io', name: 'Bob Martinez', role: 'editor', last_active: new Date().toISOString() },
  { email: 'viewer@intercom.io', name: 'Carol Wang', role: 'viewer', last_active: new Date().toISOString() },
  { email: 'guest@intercom.io', name: 'Dave Kim', role: 'guest', last_active: new Date().toISOString() },
]

const DEMO_ROLES = [
  { id: 'admin', label: 'Admin', description: 'Full access to all features and settings' },
  { id: 'editor', label: 'Editor', description: 'Can create and run simulations' },
  { id: 'viewer', label: 'Viewer', description: 'Read-only access to simulations and reports' },
  { id: 'guest', label: 'Guest', description: 'Limited access, view public content only' },
]

export const useUsersStore = defineStore('users', () => {
  const users = ref([])
  const roles = ref([])
  const loading = ref(false)
  const error = ref(null)

  const userCount = computed(() => users.value.length)
  const activeUsers = computed(() => users.value.filter(u => u.status === 'active'))

  async function fetchUsers() {
    loading.value = true
    error.value = null
    try {
      const res = await usersApi.list()
      users.value = res.data?.data || []
    } catch (e) {
      error.value = e.message || 'Failed to fetch users'
      users.value = [...DEMO_USERS]
    } finally {
      loading.value = false
    }
  }

  async function fetchRoles() {
    try {
      const res = await usersApi.roles()
      roles.value = res.data?.data || []
    } catch {
      roles.value = [...DEMO_ROLES]
    }
  }

  async function createUser(data) {
    const res = await usersApi.create(data)
    const user = res.data?.data
    if (user) users.value.unshift(user)
    return user
  }

  async function updateUser(userId, data) {
    const res = await usersApi.update(userId, data)
    const updated = res.data?.data
    if (updated) {
      const idx = users.value.findIndex(u => u.user_id === userId)
      if (idx !== -1) users.value[idx] = updated
    }
    return updated
  }

  async function deleteUser(userId) {
    await usersApi.delete(userId)
    users.value = users.value.filter(u => u.user_id !== userId)
  }

  async function updateRole(email, role) {
    try {
      await usersApi.updateRole(email, role)
      const user = users.value.find((u) => u.email === email)
      if (user) user.role = role
      return { success: true }
    } catch (err) {
      return { success: false, error: err.message || 'Failed to update role' }
    }
  }

  async function removeUser(email) {
    try {
      await usersApi.remove(email)
      users.value = users.value.filter((u) => u.email !== email)
      return { success: true }
    } catch (err) {
      return { success: false, error: err.message || 'Failed to remove user' }
    }
  }

  async function inviteUser(email, name, role) {
    try {
      const res = await usersApi.invite(email, name, role)
      const newUser = res.data?.data
      if (newUser) users.value.push(newUser)
      return { success: true }
    } catch (err) {
      return { success: false, error: err.message || 'Failed to invite user' }
    }
  }

  return {
    users,
    roles,
    loading,
    error,
    userCount,
    activeUsers,
    fetchUsers,
    fetchRoles,
    createUser,
    updateUser,
    deleteUser,
    updateRole,
    removeUser,
    inviteUser,
  }
})
