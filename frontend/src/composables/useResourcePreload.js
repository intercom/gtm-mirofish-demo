import { watch } from 'vue'
import { useRoute } from 'vue-router'

const PREFETCH_MAP = {
  landing: [
    () => import('../views/ScenarioBuilderView.vue'),
    () => import('../views/SimulationsView.vue'),
  ],
  simulations: [
    () => import('../views/ScenarioBuilderView.vue'),
  ],
  'scenario-builder': [
    () => import('../views/SimulationWorkspaceView.vue'),
  ],
  workspace: [
    () => import('../views/ReportView.vue'),
    () => import('../views/ChatView.vue'),
    () => import('../views/AgentProfileView.vue'),
  ],
  report: [
    () => import('../views/ChatView.vue'),
  ],
  chat: [
    () => import('../views/ReportView.vue'),
  ],
}

const prefetched = new Set()

function prefetchComponents(routeName) {
  if (prefetched.has(routeName)) return
  prefetched.add(routeName)

  const loaders = PREFETCH_MAP[routeName]
  if (!loaders) return

  const run = () => loaders.forEach((load) => load())

  if ('requestIdleCallback' in window) {
    requestIdleCallback(run)
  } else {
    setTimeout(run, 200)
  }
}

function addLinkHint(rel, href, attrs = {}) {
  if (document.querySelector(`link[rel="${rel}"][href="${href}"]`)) return
  const link = document.createElement('link')
  link.rel = rel
  link.href = href
  Object.assign(link, attrs)
  document.head.appendChild(link)
}

function preconnectApiOrigin() {
  const apiBase = import.meta.env.VITE_API_URL
  if (!apiBase) return

  try {
    const origin = new URL(apiBase).origin
    addLinkHint('preconnect', origin)
    addLinkHint('dns-prefetch', origin)
  } catch {
    // Relative URL — same origin, no preconnect needed
  }
}

export function useResourcePreload() {
  const route = useRoute()

  preconnectApiOrigin()

  watch(() => route.name, (name) => {
    if (name) prefetchComponents(name)
  }, { immediate: true })
}
