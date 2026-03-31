import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { ordersApi } from '../api/orders'

export const useOrdersStore = defineStore('orders', () => {
  const orders = ref([])
  const selectedOrder = ref(null)
  const billingRecords = ref([])
  const billingSummary = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // --- Getters ---

  const ordersByStatus = computed(() => {
    const grouped = {}
    for (const order of orders.value) {
      const s = order.status || 'Unknown'
      if (!grouped[s]) grouped[s] = []
      grouped[s].push(order)
    }
    return grouped
  })

  const failedOrders = computed(() =>
    orders.value.filter((o) => o.status === 'Failed'),
  )

  const avgProvisioningTime = computed(() => {
    const completed = orders.value.filter(
      (o) => o.created_date && o.activated_date,
    )
    if (completed.length === 0) return 0
    const total = completed.reduce((sum, o) => {
      const created = new Date(o.created_date)
      const activated = new Date(o.activated_date)
      return sum + (activated - created)
    }, 0)
    // Return average in hours
    return total / completed.length / (1000 * 60 * 60)
  })

  const collectionRate = computed(() => {
    if (!billingSummary.value) return 0
    return billingSummary.value.collection_rate ?? 0
  })

  // --- Actions ---

  async function fetchOrders(filters = {}) {
    loading.value = true
    error.value = null
    try {
      const { data } = await ordersApi.list(filters)
      orders.value = data.orders || []
      return orders.value
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchOrder(id) {
    loading.value = true
    error.value = null
    try {
      const { data } = await ordersApi.get(id)
      selectedOrder.value = data
      return data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchOrderTimeline(id) {
    loading.value = true
    error.value = null
    try {
      const { data } = await ordersApi.getTimeline(id)
      if (selectedOrder.value?.id === id) {
        selectedOrder.value = { ...selectedOrder.value, timeline: data.timeline || [] }
      }
      return data.timeline || []
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function retryProvisioning(id) {
    loading.value = true
    error.value = null
    try {
      const { data } = await ordersApi.retryProvisioning(id)
      // Refresh the order after retry
      const idx = orders.value.findIndex((o) => o.id === id)
      if (idx !== -1 && data.order) {
        orders.value[idx] = data.order
      }
      if (selectedOrder.value?.id === id && data.order) {
        selectedOrder.value = data.order
      }
      return data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  async function fetchBilling(filters = {}) {
    loading.value = true
    error.value = null
    try {
      const { data } = await ordersApi.getBilling(filters)
      billingRecords.value = data.records || []
      return billingRecords.value
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function fetchBillingSummary() {
    loading.value = true
    error.value = null
    try {
      const { data } = await ordersApi.getBillingSummary()
      billingSummary.value = data
      return data
    } catch (e) {
      error.value = e.message
      return null
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    orders,
    selectedOrder,
    billingRecords,
    billingSummary,
    loading,
    error,
    // Getters
    ordersByStatus,
    failedOrders,
    avgProvisioningTime,
    collectionRate,
    // Actions
    fetchOrders,
    fetchOrder,
    fetchOrderTimeline,
    retryProvisioning,
    fetchBilling,
    fetchBillingSummary,
  }
})
