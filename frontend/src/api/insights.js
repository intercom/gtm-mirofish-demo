import client from './client'

export const insightsApi = {
  chat: (data) => client.post('/insights/chat', data),
}
