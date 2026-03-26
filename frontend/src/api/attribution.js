import client from './client'

export const attributionApi = {
  getAnalysis: (simulationId) =>
    client.get('/v1/attribution/analysis', {
      params: simulationId ? { simulation_id: simulationId } : {},
    }),
}
