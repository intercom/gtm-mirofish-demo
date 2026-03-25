import { computed } from 'vue'
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
