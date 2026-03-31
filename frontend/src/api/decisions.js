import client from './client'

export const decisionsApi = {
  explain: (data) => client.post('/decisions/explain', data),
  counterfactual: (data) => client.post('/decisions/counterfactual', data),
  score: (data) => client.post('/decisions/score', data),
}
