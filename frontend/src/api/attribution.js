import client from './client'

export const attributionApi = {
  getAnalysis: (simulationId) =>
    client.get('/attribution/analysis', {
      params: simulationId ? { simulation_id: simulationId } : {},
    }),
}
