import client from './client'

export const whatifApi = {
  run: (data) => client.post('/simulation/whatif', data),
  getVariants: (simulationId) =>
    client.get(`/simulation/${simulationId}/whatif/variants`),
  runSensitivity: (data) => client.post('/simulation/sensitivity', data),
  getSensitivity: (simulationId) =>
    client.get(`/simulation/${simulationId}/sensitivity`),
  getTornado: (simulationId) =>
    client.get(`/simulation/${simulationId}/tornado`),
}
