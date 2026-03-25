import { ref } from 'vue'
import { useRouter } from 'vue-router'

const ROUTE_DEPTH = {
  landing: 0,
  simulations: 1,
  settings: 1,
  'scenario-builder': 2,
  workspace: 3,
  report: 3,
  chat: 3,
  'agent-profile': 4,
}

export function usePageTransition() {
  const router = useRouter()
  const transitionName = ref('page-fade')

  router.beforeEach((to, from) => {
    const toDepth = ROUTE_DEPTH[to.name] ?? 1
    const fromDepth = ROUTE_DEPTH[from.name] ?? 1

    if (toDepth > fromDepth) {
      transitionName.value = 'page-slide-left'
    } else if (toDepth < fromDepth) {
      transitionName.value = 'page-slide-right'
    } else {
      transitionName.value = 'page-fade'
    }
  })

  return { transitionName }
}
