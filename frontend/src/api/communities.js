import client from './client'

export const communitiesApi = {
  detect: (graphId) => client.get(`/graph/communities/${graphId}`),
}
