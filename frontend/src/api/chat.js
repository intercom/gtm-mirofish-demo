import client from './client'

export const chatApi = {
  send: (data) => client.post('/report/chat', data),
}
