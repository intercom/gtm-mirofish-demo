import client from './client'

const PREFIX = '/v1/memory'

export const memoryApi = {
  getConfig: () => client.get(`${PREFIX}/config`),
  saveConfig: (data) => client.post(`${PREFIX}/config`, data),
  getStats: (params) => client.get(`${PREFIX}/stats`, { params }),
  testConnection: (data) => client.post(`${PREFIX}/test-connection`, data),
}
