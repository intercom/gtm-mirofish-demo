import client from './client'

export const pipelineApi = {
  // --- Funnel ---
  getFunnel: () =>
    client.get('/api/v1/pipeline/funnel'),

  getFunnelHistory: (months) =>
    client.get('/api/v1/pipeline/funnel/history', { params: { months } }),

  // --- Conversions ---
  getConversions: (params) =>
    client.get('/api/v1/pipeline/conversions', { params }),

  // --- Velocity ---
  getVelocity: () =>
    client.get('/api/v1/pipeline/velocity'),

  // --- Forecast ---
  getForecast: () =>
    client.get('/api/v1/pipeline/forecast'),
}
