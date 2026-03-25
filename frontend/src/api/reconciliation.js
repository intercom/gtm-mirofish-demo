import client from './client'

export const reconciliationApi = {
  // --- Runs ---
  listRuns: (params) => client.get('/reconciliation/runs', { params }),
  getRun: (runId) => client.get(`/reconciliation/runs/${runId}`),
  getCurrent: () => client.get('/reconciliation/current'),

  // --- Discrepancies ---
  listDiscrepancies: (params) =>
    client.get('/reconciliation/discrepancies', { params }),
  resolve: (recordId, data) =>
    client.post(`/reconciliation/resolve/${recordId}`, data),

  // --- Account detail ---
  getAccount: (accountId) =>
    client.get(`/reconciliation/account/${accountId}`),

  // --- Rules & stats ---
  getRules: () => client.get('/reconciliation/rules'),
  getStats: () => client.get('/reconciliation/stats'),
}
