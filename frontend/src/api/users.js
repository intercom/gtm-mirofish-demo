import client from './client'

export const usersApi = {
  list: () => client.get('/v1/users'),
  roles: () => client.get('/v1/users/roles'),
  updateRole: (email, role) => client.put(`/v1/users/${encodeURIComponent(email)}/role`, { role }),
  remove: (email) => client.delete(`/v1/users/${encodeURIComponent(email)}`),
  invite: (email, name, role) => client.post('/v1/users/invite', { email, name, role }),
}
