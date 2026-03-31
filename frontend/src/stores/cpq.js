import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { cpqApi } from '../api/cpq'

export const useCpqStore = defineStore('cpq', () => {
  const products = ref([])
  const quotes = ref([])
  const selectedQuote = ref(null)
  const stats = ref({})
  const loading = ref(false)
  const error = ref(null)

  const quotesByStatus = computed(() => {
    const grouped = {}
    for (const quote of quotes.value) {
      const status = quote.status || 'unknown'
      if (!grouped[status]) grouped[status] = []
      grouped[status].push(quote)
    }
    return grouped
  })

  const productsByFamily = computed(() => {
    const grouped = {}
    for (const product of products.value) {
      const family = product.family || 'Other'
      if (!grouped[family]) grouped[family] = []
      grouped[family].push(product)
    }
    return grouped
  })

  const totalPipelineValue = computed(() =>
    quotes.value.reduce((sum, q) => sum + (q.total_value || 0), 0),
  )

  const avgDiscount = computed(() => {
    if (quotes.value.length === 0) return 0
    const total = quotes.value.reduce((sum, q) => sum + (q.discount || 0), 0)
    return total / quotes.value.length
  })

  const approvalRate = computed(() => {
    if (quotes.value.length === 0) return 0
    const approved = quotes.value.filter(
      (q) => q.status === 'approved',
    ).length
    return approved / quotes.value.length
  })

  async function fetchProducts() {
    loading.value = true
    error.value = null
    try {
      const res = await cpqApi.getProducts()
      products.value = res.data.products || []
      return products.value
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchQuotes(filters = {}) {
    loading.value = true
    error.value = null
    try {
      const res = await cpqApi.getQuotes(filters)
      quotes.value = res.data.quotes || []
      return quotes.value
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchQuote(id) {
    loading.value = true
    error.value = null
    try {
      const res = await cpqApi.getQuote(id)
      selectedQuote.value = res.data
      return res.data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function approveQuote(id) {
    loading.value = true
    error.value = null
    try {
      const res = await cpqApi.approveQuote(id)
      const idx = quotes.value.findIndex((q) => q.id === id)
      if (idx !== -1)
        quotes.value[idx] = { ...quotes.value[idx], status: 'approved' }
      if (selectedQuote.value?.id === id)
        selectedQuote.value = { ...selectedQuote.value, status: 'approved' }
      return res.data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function rejectQuote(id, reason) {
    loading.value = true
    error.value = null
    try {
      const res = await cpqApi.rejectQuote(id, reason)
      const idx = quotes.value.findIndex((q) => q.id === id)
      if (idx !== -1)
        quotes.value[idx] = {
          ...quotes.value[idx],
          status: 'rejected',
          rejection_reason: reason,
        }
      if (selectedQuote.value?.id === id)
        selectedQuote.value = {
          ...selectedQuote.value,
          status: 'rejected',
          rejection_reason: reason,
        }
      return res.data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchCpqStats() {
    loading.value = true
    error.value = null
    try {
      const res = await cpqApi.getCpqStats()
      stats.value = res.data
      return stats.value
    } catch (e) {
      error.value = e.message
      return {}
    } finally {
      loading.value = false
    }
  }

  return {
    products,
    quotes,
    selectedQuote,
    stats,
    loading,
    error,
    quotesByStatus,
    productsByFamily,
    totalPipelineValue,
    avgDiscount,
    approvalRate,
    fetchProducts,
    fetchQuotes,
    fetchQuote,
    approveQuote,
    rejectQuote,
    fetchCpqStats,
  }
})
