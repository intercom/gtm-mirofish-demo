import client from './client'

export const usersApi = {
  list: () => client.get('/v1/users'),
  get: (userId) => client.get(`/v1/users/${userId}`),
  create: (data) => client.post('/v1/users', data),
  update: (userId, data) => client.put(`/v1/users/${userId}`, data),
  delete: (userId) => client.delete(`/v1/users/${userId}`),
}
