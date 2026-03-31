import { ref, computed } from 'vue'
import { useAuthStore } from '../stores/auth'

const ROLE_HIERARCHY = ['guest', 'viewer', 'editor', 'admin']

const ROLE_PERMISSIONS = {
  admin: [
    'view_simulations', 'create_simulations', 'edit_simulations', 'delete_simulations',
    'view_reports', 'create_reports',
    'manage_agents', 'manage_templates', 'manage_settings', 'manage_users', 'manage_api_keys',
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

  const role = computed(() => {
    if (!auth.user) return 'admin'
    return auth.user.role || 'guest'
  })

  const permissions = computed(() => {
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
  const isReadOnly = computed(() => !hasRole('editor'))

  return { role, permissions, can, hasRole, isAdmin, isEditor, isViewer, isReadOnly, ROLE_HIERARCHY, ROLE_PERMISSIONS }
}

export function useApiPermissions() {
  const permissions = ref({})

  function updatePermissions(perms) {
    if (perms && typeof perms === 'object') {
      permissions.value = perms
    }
  }

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

export function extractPermissions(response) {
  const data = response?.data?.data ?? response?.data
  if (!data) return {}
  if (Array.isArray(data)) {
    return data[0]?.permissions ?? {}
  }
  return data.permissions ?? {}
}
