import { computed, unref } from 'vue'
import { useRoute } from 'vue-router'

const routeLabels = {
  landing: 'Home',
  simulations: 'Simulations',
  settings: 'Settings',
  'scenario-builder': 'Scenario Builder',
  workspace: 'Workspace',
  report: 'Report',
  chat: 'Chat',
  'agent-profile': 'Agent',
}

/**
 * Builds breadcrumb trail from the current route.
 * Views can pass overrides to replace default labels with dynamic values
 * (e.g. a scenario name instead of "Workspace").
 *
 * @param {Object|import('vue').Ref<Object>} overrides - Map of route names to custom labels (plain object or ref/computed)
 * @returns {{ crumbs: import('vue').ComputedRef<Array<{ label: string, to?: string }>> }}
 */
export function useBreadcrumbs(overrides = {}) {
  const route = useRoute()

  const crumbs = computed(() => {
    const o = unref(overrides)
    const name = route.name
    if (!name || name === 'landing') return []

    const items = [{ label: 'Home', to: '/' }]

    // Task-scoped routes share a common parent trail
    const taskId = route.params.taskId
    if (taskId) {
      items.push({ label: 'Simulations', to: '/simulations' })
    }

    // Scenario builder links back to landing (scenarios are entry points)
    if (name === 'scenario-builder') {
      items.push({ label: o['scenario-builder'] || 'Scenario Builder' })
      return items
    }

    if (name === 'workspace') {
      items.push({ label: o.workspace || 'Workspace' })
      return items
    }

    if (name === 'report') {
      items.push({
        label: o.workspace || 'Workspace',
        to: `/workspace/${taskId}`,
      })
      items.push({ label: o.report || 'Report' })
      return items
    }

    if (name === 'chat') {
      items.push({
        label: o.workspace || 'Workspace',
        to: `/workspace/${taskId}`,
      })
      items.push({ label: o.chat || 'Chat' })
      return items
    }

    if (name === 'agent-profile') {
      items.push({
        label: o.workspace || 'Workspace',
        to: `/workspace/${taskId}`,
      })
      items.push({ label: o['agent-profile'] || 'Agent' })
      return items
    }

    // Top-level pages (simulations, settings)
    const label = o[name] || routeLabels[name] || name
    items.push({ label })
    return items
  })

  return { crumbs }
}
