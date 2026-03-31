import client from './client'

export const pipelineApi = {
  // --- Funnel ---
  getFunnel: () =>
    client.get('/pipeline/funnel'),

  getFunnelHistory: (months) =>
    client.get('/pipeline/funnel/history', { params: { months } }),

  // --- Conversions ---
  getConversions: (params) =>
    client.get('/pipeline/conversions', { params }),

  // --- Velocity ---
  getVelocity: () =>
    client.get('/pipeline/velocity'),

  // --- Forecast ---
  getForecast: () =>
    client.get('/pipeline/forecast'),
}
