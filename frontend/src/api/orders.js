import client from './client'

export const ordersApi = {
  // --- Orders ---
  list: (params) => client.get('/orders', { params }),
  get: (orderId) => client.get(`/orders/${orderId}`),
  getTimeline: (orderId) => client.get(`/orders/${orderId}/timeline`),
  retryProvisioning: (orderId) => client.post(`/orders/${orderId}/retry-provisioning`),

  // --- Billing ---
  getBilling: (params) => client.get('/billing', { params }),
  getBillingSummary: () => client.get('/billing/summary'),
}
