import { computed } from 'vue'
import { useAuthStore } from '../stores/auth'

const ROLES = ['guest', 'viewer', 'editor', 'admin']

const ROLE_PERMISSIONS = {
  admin: [
    'view_simulations', 'create_simulations', 'edit_simulations', 'delete_simulations',
    'view_reports', 'create_reports',
    'manage_agents', 'manage_templates', 'manage_settings', 'manage_users',
  ],
  editor: [
    'view_simulations', 'create_simulations', 'edit_simulations', 'delete_simulations',
    'view_reports', 'create_reports',
    'manage_agents', 'manage_templates',
  ],
  viewer: ['view_simulations', 'view_reports'],
  guest: ['view_simulations', 'view_reports'],
}

export function usePermissions() {
  const auth = useAuthStore()

  const userRole = computed(() => {
    if (!auth.user) return 'admin'
    return auth.user.role || 'guest'
  })

  function can(permission) {
    const permissions = ROLE_PERMISSIONS[userRole.value] || []
    return permissions.includes(permission)
  }

  function hasRole(role) {
    const currentLevel = ROLES.indexOf(userRole.value)
    const requiredLevel = ROLES.indexOf(role)
    if (currentLevel === -1 || requiredLevel === -1) return false
    return currentLevel >= requiredLevel
  }

  const isReadOnly = computed(() => !hasRole('editor'))

  return { userRole, can, hasRole, isReadOnly, ROLES, ROLE_PERMISSIONS }
}
