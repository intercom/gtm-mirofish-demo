import client from './client'

export const analyticsApi = {
  // --- Cohort analysis ---
  getCohorts: (params) => client.get('/analytics/cohorts', { params }),
  compareCohorts: (params) => client.get('/analytics/cohorts/compare', { params }),

  // --- Segment performance ---
  getSegments: (type = 'plan_tier') =>
    client.get('/analytics/segments', { params: { type } }),

  getSegmentAccounts: (segmentType, segmentName) =>
    client.get(`/analytics/segments/${segmentType}/${encodeURIComponent(segmentName)}/accounts`),

  // --- Anomaly detection ---
  getAnomalies: (params = {}) => client.get('/analytics/anomalies', { params }),
}
