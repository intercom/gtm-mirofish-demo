import client from './client'

export const reconciliationApi = {
  getTrend: (params) => client.get('/reconciliation/trend', { params }),
}
