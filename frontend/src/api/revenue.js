import client from './client'

export const revenueApi = {
  getMetrics: (params) => client.get('/revenue/metrics', { params }),
  getCustomers: (params) => client.get('/revenue/customers', { params }),
  getChurnEvents: (params) => client.get('/revenue/churn', { params }),
  getExpansionEvents: (params) => client.get('/revenue/expansion', { params }),
  getSummary: () => client.get('/revenue/summary'),
  getCohortData: () => client.get('/revenue/cohort'),
}
