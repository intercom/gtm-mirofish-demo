import { ref, computed } from 'vue'

/**
 * Composable for extracting and checking permissions from API responses.
 *
 * API responses include a `permissions` object like:
 *   { "can_view": true, "can_edit": true, "can_delete": false }
 *
 * Usage:
 *   const { permissions, updatePermissions, can } = usePermissions()
 *   // After an API call:
 *   updatePermissions(response.data.permissions)
 *   // In template:
 *   v-if="can('delete')"
 */
export function usePermissions() {
  const permissions = ref({})

  function updatePermissions(perms) {
    if (perms && typeof perms === 'object') {
      permissions.value = perms
    }
  }

  /**
   * Check if an action is permitted.
   * Accepts either 'edit' or 'can_edit' format.
   */
  function can(action) {
    const key = action.startsWith('can_') ? action : `can_${action}`
    return permissions.value[key] === true
  }

  const canView = computed(() => can('view'))
  const canEdit = computed(() => can('edit'))
  const canCreate = computed(() => can('create'))
  const canDelete = computed(() => can('delete'))

  return {
    permissions,
    updatePermissions,
    can,
    canView,
    canEdit,
    canCreate,
    canDelete,
  }
}

/**
 * Extract permissions from a standard API response.
 * Works with both single-item and list responses.
 *
 * For single: response.data.data.permissions
 * For list: response.data.data[0].permissions (first item)
 * For non-standard: response.data.permissions
 */
export function extractPermissions(response) {
  const data = response?.data?.data ?? response?.data
  if (!data) return {}
  if (Array.isArray(data)) {
    return data[0]?.permissions ?? {}
  }
  return data.permissions ?? {}
}
