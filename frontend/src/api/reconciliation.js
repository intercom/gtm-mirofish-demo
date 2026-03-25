import client from './client'

const MOCK_RECORDS = [
  { id: 'ACC-001', account: 'Acme Corp', salesforce_mrr: 12500, billing_mrr: 12500, snowflake_mrr: 12500, discrepancy_type: null, resolution: null, resolved: false, last_updated: '2026-03-22' },
  { id: 'ACC-002', account: 'TechFlow Inc', salesforce_mrr: 8750, billing_mrr: 8750, snowflake_mrr: 8690, discrepancy_type: 'rounding', resolution: null, resolved: false, last_updated: '2026-03-22' },
  { id: 'ACC-003', account: 'GlobalServe Ltd', salesforce_mrr: 34200, billing_mrr: 33800, snowflake_mrr: 34200, discrepancy_type: 'timing', resolution: null, resolved: false, last_updated: '2026-03-21' },
  { id: 'ACC-004', account: 'DataDriven Co', salesforce_mrr: 5600, billing_mrr: 5600, snowflake_mrr: 5600, discrepancy_type: null, resolution: null, resolved: false, last_updated: '2026-03-22' },
  { id: 'ACC-005', account: 'CloudNine Systems', salesforce_mrr: 22100, billing_mrr: 21200, snowflake_mrr: 22100, discrepancy_type: 'timing', resolution: null, resolved: false, last_updated: '2026-03-20' },
  { id: 'ACC-006', account: 'Pinnacle Ventures', salesforce_mrr: 15800, billing_mrr: 15800, snowflake_mrr: 15800, discrepancy_type: null, resolution: null, resolved: false, last_updated: '2026-03-22' },
  { id: 'ACC-007', account: 'NexGen Analytics', salesforce_mrr: 9200, billing_mrr: 9200, snowflake_mrr: 9150, discrepancy_type: 'rounding', resolution: null, resolved: false, last_updated: '2026-03-22' },
  { id: 'ACC-008', account: 'Bright Horizons SaaS', salesforce_mrr: 41500, billing_mrr: 40200, snowflake_mrr: 39800, discrepancy_type: 'genuine', resolution: null, resolved: false, last_updated: '2026-03-19' },
  { id: 'ACC-009', account: 'Velocity Partners', salesforce_mrr: 7300, billing_mrr: 7300, snowflake_mrr: 7300, discrepancy_type: null, resolution: null, resolved: false, last_updated: '2026-03-22' },
  { id: 'ACC-010', account: 'Summit Enterprises', salesforce_mrr: 18900, billing_mrr: 18900, snowflake_mrr: 18900, discrepancy_type: null, resolution: null, resolved: false, last_updated: '2026-03-22' },
  { id: 'ACC-011', account: 'Quantum Dynamics', salesforce_mrr: 28400, billing_mrr: 27100, snowflake_mrr: 28400, discrepancy_type: 'timing', resolution: null, resolved: false, last_updated: '2026-03-21' },
  { id: 'ACC-012', account: 'FreshStart Labs', salesforce_mrr: 3200, billing_mrr: 3200, snowflake_mrr: 3200, discrepancy_type: null, resolution: null, resolved: false, last_updated: '2026-03-22' },
  { id: 'ACC-013', account: 'Atlas Digital', salesforce_mrr: 67500, billing_mrr: 67500, snowflake_mrr: 65200, discrepancy_type: 'genuine', resolution: null, resolved: false, last_updated: '2026-03-18' },
  { id: 'ACC-014', account: 'RapidScale Corp', salesforce_mrr: 11000, billing_mrr: 10950, snowflake_mrr: 11000, discrepancy_type: 'rounding', resolution: null, resolved: false, last_updated: '2026-03-22' },
  { id: 'ACC-015', account: 'Evergreen Solutions', salesforce_mrr: 4800, billing_mrr: 4800, snowflake_mrr: 4800, discrepancy_type: null, resolution: null, resolved: false, last_updated: '2026-03-22' },
  { id: 'ACC-016', account: 'OmniChannel Pro', salesforce_mrr: 19600, billing_mrr: 18400, snowflake_mrr: 19600, discrepancy_type: 'missing', resolution: null, resolved: false, last_updated: '2026-03-20' },
  { id: 'ACC-017', account: 'SilverLine Tech', salesforce_mrr: 8100, billing_mrr: 8100, snowflake_mrr: 8100, discrepancy_type: null, resolution: null, resolved: false, last_updated: '2026-03-22' },
  { id: 'ACC-018', account: 'CoreLogic Systems', salesforce_mrr: 52000, billing_mrr: 52000, snowflake_mrr: 50500, discrepancy_type: 'genuine', resolution: null, resolved: false, last_updated: '2026-03-19' },
  { id: 'ACC-019', account: 'BlueShift AI', salesforce_mrr: 14300, billing_mrr: 14300, snowflake_mrr: 14300, discrepancy_type: null, resolution: null, resolved: false, last_updated: '2026-03-22' },
  { id: 'ACC-020', account: 'Horizon CX Group', salesforce_mrr: 25700, billing_mrr: 24900, snowflake_mrr: 25700, discrepancy_type: 'timing', resolution: null, resolved: false, last_updated: '2026-03-21' },
]

function mockResponse(data, delay = 300) {
  return new Promise((resolve) =>
    setTimeout(() => resolve({ data }), delay),
  )
}

export const reconciliationApi = {
  // --- Runs ---
  listRuns: (params) => client.get('/reconciliation/runs', { params }),
  getRun: (runId) => client.get(`/reconciliation/runs/${runId}`),
  getCurrent: () =>
    client.get('/reconciliation/current').catch(() =>
      mockResponse({ records: MOCK_RECORDS }),
    ),

  // --- Discrepancies ---
  listDiscrepancies: (params) =>
    client.get('/reconciliation/discrepancies', { params }).catch(() =>
      mockResponse({
        records: MOCK_RECORDS.filter(
          (r) => r.discrepancy_type !== null,
        ),
      }),
    ),
  resolve: (recordId, data) =>
    client.post(`/reconciliation/resolve/${recordId}`, data).catch(() =>
      mockResponse({ success: true }),
    ),

  // --- Account detail ---
  getAccount: (accountId) =>
    client.get(`/reconciliation/account/${accountId}`),

  // --- Rules & stats ---
  getRules: () => client.get('/reconciliation/rules'),
  getStats: () => client.get('/reconciliation/stats'),
}
