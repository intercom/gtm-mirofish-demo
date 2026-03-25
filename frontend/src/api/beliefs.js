import client from './client'

export const beliefsApi = {
  getDimensions: () =>
    client.get('/v1/beliefs/dimensions'),

  extract: (simulationId, actions, useLlm = false) =>
    client.post(`/v1/beliefs/${simulationId}/extract`, {
      actions,
      use_llm: useLlm,
    }),

  demo: (rounds = 10) =>
    client.get('/v1/beliefs/demo', { params: { rounds } }),
}
