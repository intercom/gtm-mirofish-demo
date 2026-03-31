import client from './client'

const BASE = '/sessions'

export const sessionsApi = {
  list: (params) => client.get(BASE, { params }),
  create: (data) => client.post(BASE, data),
  get: (sessionId) => client.get(`${BASE}/${sessionId}`),
  update: (sessionId, data) => client.put(`${BASE}/${sessionId}`, data),
  delete: (sessionId) => client.delete(`${BASE}/${sessionId}`),
  addSimulation: (sessionId, simulationId) =>
    client.post(`${BASE}/${sessionId}/simulations`, { simulation_id: simulationId }),
}
