import client from './client'

export const metricsApi = {
  getSimulationMetrics: (simulationId, params) =>
    client.get(`/metrics/simulation/${simulationId}`, { params }),

  getDemoMetrics: () =>
    client.get('/metrics/demo'),
}
