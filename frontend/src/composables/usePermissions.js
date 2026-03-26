import { ref, computed } from 'vue'
import { useAuthStore } from '../stores/auth'

/**
 * Role hierarchy and permission mapping — mirrors backend/auth/rbac.py.
 * Keep these in sync when roles or permissions change.
 */

const ROLE_HIERARCHY = ['guest', 'viewer', 'editor', 'admin']

const ROLE_PERMISSIONS = {
  guest: ['view_simulations', 'view_reports'],
  viewer: ['view_simulations', 'view_reports'],
  editor: [
    'view_simulations', 'create_simulations', 'edit_simulations', 'delete_simulations',
    'view_reports', 'create_reports',
    'manage_agents', 'manage_templates',
  ],
  admin: [
    'view_simulations', 'create_simulations', 'edit_simulations', 'delete_simulations',
    'view_reports', 'create_reports',
    'manage_agents', 'manage_templates',
    'manage_settings', 'manage_users', 'manage_api_keys',
  ],
}

export function usePermissions() {
  const auth = useAuthStore()

  const role = computed(() => auth.user?.role || 'guest')

  const permissions = computed(() => {
    // Prefer server-provided permissions, fall back to local mapping
    if (auth.user?.permissions?.length) return auth.user.permissions
    return ROLE_PERMISSIONS[role.value] || []
  })

  function can(permission) {
    return permissions.value.includes(permission)
  }

  function hasRole(requiredRole) {
    return ROLE_HIERARCHY.indexOf(role.value) >= ROLE_HIERARCHY.indexOf(requiredRole)
  }

  const isAdmin = computed(() => role.value === 'admin')
  const isEditor = computed(() => hasRole('editor'))
  const isViewer = computed(() => hasRole('viewer'))

  return { role, permissions, can, hasRole, isAdmin, isEditor, isViewer }
}

/**
 * Composable for extracting and checking permissions from API responses.
 *
 * API responses include a `permissions` object like:
 *   { "can_view": true, "can_edit": true, "can_delete": false }
 *
 * Usage:
 *   const { permissions, updatePermissions, can } = useApiPermissions()
 *   // After an API call:
 *   updatePermissions(response.data.permissions)
 *   // In template:
 *   v-if="can('delete')"
 */
export function useApiPermissions() {
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
