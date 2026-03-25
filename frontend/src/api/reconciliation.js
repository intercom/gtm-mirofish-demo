import client from './client'

export const reconciliationApi = {
  getDiscrepancyDistribution: (params) =>
    client.get('/v1/reconciliation/discrepancy-distribution', { params }),
}
