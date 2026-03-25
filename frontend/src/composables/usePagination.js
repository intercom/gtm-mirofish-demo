import { ref, computed, watch } from 'vue'

/**
 * Generic client-side pagination composable.
 *
 * @param {import('vue').Ref|import('vue').ComputedRef} source - reactive array of items
 * @param {object} [options]
 * @param {number}  [options.perPage=10]  - items per page
 */
export function usePagination(source, options = {}) {
  const perPage = ref(options.perPage ?? 10)
  const currentPage = ref(1)

  const total = computed(() => source.value.length)
  const totalPages = computed(() => Math.max(1, Math.ceil(total.value / perPage.value)))

  const paginatedItems = computed(() => {
    const start = (currentPage.value - 1) * perPage.value
    return source.value.slice(start, start + perPage.value)
  })

  const hasNextPage = computed(() => currentPage.value < totalPages.value)
  const hasPrevPage = computed(() => currentPage.value > 1)

  function goToPage(page) {
    currentPage.value = Math.max(1, Math.min(page, totalPages.value))
  }

  function nextPage() {
    if (hasNextPage.value) currentPage.value++
  }

  function prevPage() {
    if (hasPrevPage.value) currentPage.value--
  }

  // Reset to page 1 when the source data changes (e.g. filter applied)
  watch([source, perPage], () => {
    if (currentPage.value > totalPages.value) {
      currentPage.value = Math.max(1, totalPages.value)
    }
  })

  return {
    currentPage,
    perPage,
    total,
    totalPages,
    paginatedItems,
    hasNextPage,
    hasPrevPage,
    goToPage,
    nextPage,
    prevPage,
  }
}
