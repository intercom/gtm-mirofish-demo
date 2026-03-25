import client from './client'

export const decisionsApi = {
  explain: (data) => client.post('/v1/decisions/explain', data),
  counterfactual: (data) => client.post('/v1/decisions/counterfactual', data),
  score: (data) => client.post('/v1/decisions/score', data),
}
