import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { usersApi } from '../api/users'

export const useUsersStore = defineStore('users', () => {
  const users = ref([])
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
    } finally {
      loading.value = false
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

  return {
    users,
    loading,
    error,
    userCount,
    activeUsers,
    fetchUsers,
    createUser,
    updateUser,
    deleteUser,
  }
})
