import client from './client'

export const metricsApi = {
  getSimulationMetrics: (simulationId, params) =>
    client.get(`/v1/metrics/simulation/${simulationId}`, { params }),

  getDemoMetrics: () =>
    client.get('/v1/metrics/demo'),
}
