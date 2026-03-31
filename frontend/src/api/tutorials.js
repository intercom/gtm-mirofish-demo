import client from './client'

export const tutorialsApi = {
  list: (category) =>
    client.get('/tutorials/', { params: category ? { category } : {} }),
  get: (tutorialId) => client.get(`/tutorials/${tutorialId}`),
  validateStep: (tutorialId, stepId) =>
    client.post(`/tutorials/${tutorialId}/steps/${stepId}/validate`),
}
