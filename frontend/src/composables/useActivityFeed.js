import { onMounted, onUnmounted } from 'vue'
import { useActivityStore } from '../stores/activity'

/**
 * Composable for consuming the global activity feed with optional auto-refresh.
 *
 * @param {Object} opts
 * @param {number} opts.limit        - Max items to fetch (default 20)
 * @param {string[]} opts.types      - Activity types to filter by
 * @param {number} opts.pollInterval - Auto-refresh interval in ms (0 = disabled, default 60000)
 */
export function useActivityFeed(opts = {}) {
  const store = useActivityStore()

  const limit = opts.limit ?? 20
  const types = opts.types ?? []
  const pollInterval = opts.pollInterval ?? 60_000

  let timer = null

  async function refresh() {
    return store.fetchRecent({ limit, types })
  }

  onMounted(() => {
    refresh()
    if (pollInterval > 0) {
      timer = setInterval(refresh, pollInterval)
    }
  })

  onUnmounted(() => {
    if (timer) {
      clearInterval(timer)
      timer = null
    }
  })

  return {
    items: store.items,
    loading: store.loading,
    error: store.error,
    hasItems: store.hasItems,
    criticalCount: store.criticalCount,
    warningCount: store.warningCount,
    refresh,
  }
}
