import client from './client'

export const usersApi = {
  list: () => client.get('/v1/users'),
  get: (userId) => client.get(`/v1/users/${userId}`),
  create: (data) => client.post('/v1/users', data),
  update: (userId, data) => client.put(`/v1/users/${userId}`, data),
  delete: (userId) => client.delete(`/v1/users/${userId}`),
  roles: () => client.get('/v1/users/roles'),
  updateRole: (email, role) => client.put(`/v1/users/${encodeURIComponent(email)}/role`, { role }),
  remove: (email) => client.delete(`/v1/users/${encodeURIComponent(email)}`),
  invite: (email, name, role) => client.post('/v1/users/invite', { email, name, role }),
}
