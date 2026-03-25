import { ref } from 'vue'
import { useRouter } from 'vue-router'

const ROUTE_DEPTH = {
  landing: 0,
  simulations: 1,
  settings: 1,
  'scenario-builder': 2,
  workspace: 3,
  'agent-profile': 4,
  report: 4,
  chat: 4,
}

export function usePageTransition() {
  const router = useRouter()
  const transitionName = ref('page-forward')

  router.beforeEach((to, from) => {
    const toDepth = ROUTE_DEPTH[to.name] ?? 0
    const fromDepth = ROUTE_DEPTH[from.name] ?? 0
    transitionName.value = toDepth >= fromDepth ? 'page-forward' : 'page-back'
  })

  return { transitionName }
}
