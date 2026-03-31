import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('../../api/agents', () => ({
  agentsApi: {
    list: vi.fn(),
    delete: vi.fn(),
    generate: vi.fn(),
    listArchetypes: vi.fn(),
    createFromArchetype: vi.fn(),
    createBatch: vi.fn(),
    createFromScenario: vi.fn(),
  },
}))

import { useAgentsStore } from '../agents'
import { agentsApi } from '../../api/agents'

const STORAGE_KEY = 'mirofish_custom_agents'

function makeAgent(overrides = {}) {
  return {
    id: `agent-${Math.random().toString(36).slice(2, 8)}`,
    name: 'Test Agent',
    role: 'Tester',
    department: 'Engineering',
    ...overrides,
  }
}

describe('useAgentsStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  // --- Initial state ---

  it('initialises with empty agents and no loading/error', () => {
    const store = useAgentsStore()
    expect(store.agents).toEqual([])
    expect(store.archetypes).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  // --- templates computed ---

  it('templates returns the built-in TEMPLATE_AGENTS', () => {
    const store = useAgentsStore()
    expect(store.templates.length).toBeGreaterThan(0)
    expect(store.templates.every((t) => t.is_template === true)).toBe(true)
    expect(store.templates.some((t) => t.id === 'tmpl-vp-support')).toBe(true)
  })

  // --- hasAgents computed ---

  it('hasAgents is false when no agents exist', () => {
    const store = useAgentsStore()
    expect(store.hasAgents).toBe(false)
  })

  it('hasAgents is true after adding an agent', () => {
    const store = useAgentsStore()
    store.addAgent(makeAgent())
    expect(store.hasAgents).toBe(true)
  })

  // --- allDepartments computed ---

  it('allDepartments includes default departments sorted', () => {
    const store = useAgentsStore()
    const depts = store.allDepartments
    expect(depts).toContain('Sales')
    expect(depts).toContain('Marketing')
    expect(depts).toContain('CS')
    expect(depts).toContain('Engineering')
    expect(depts).toEqual([...depts].sort())
  })

  it('allDepartments merges custom agent departments', () => {
    const store = useAgentsStore()
    store.addAgent(makeAgent({ department: 'Legal' }))
    expect(store.allDepartments).toContain('Legal')
  })

  // --- allRoles computed ---

  it('allRoles includes roles from both agents and templates', () => {
    const store = useAgentsStore()
    store.addAgent(makeAgent({ role: 'Custom Role' }))
    const roles = store.allRoles
    expect(roles).toContain('Custom Role')
    expect(roles).toContain('VP of Customer Support')
    expect(roles).toEqual([...roles].sort())
  })

  // --- archetypeCount / agentCount computed ---

  it('archetypeCount reflects archetypes array length', () => {
    const store = useAgentsStore()
    expect(store.archetypeCount).toBe(0)
    store.archetypes = [{ id: 'a1', category: 'buyer' }]
    expect(store.archetypeCount).toBe(1)
  })

  it('agentCount reflects agents array length', () => {
    const store = useAgentsStore()
    expect(store.agentCount).toBe(0)
    store.addAgent(makeAgent())
    expect(store.agentCount).toBe(1)
  })

  // --- archetypesByCategory computed ---

  it('archetypesByCategory groups by category', () => {
    const store = useAgentsStore()
    store.archetypes = [
      { id: 'a1', category: 'buyer' },
      { id: 'a2', category: 'seller' },
      { id: 'a3', category: 'buyer' },
    ]
    const grouped = store.archetypesByCategory
    expect(grouped.buyer).toHaveLength(2)
    expect(grouped.seller).toHaveLength(1)
  })

  it('archetypesByCategory uses "other" for missing category', () => {
    const store = useAgentsStore()
    store.archetypes = [{ id: 'a1' }]
    const grouped = store.archetypesByCategory
    expect(grouped.other).toHaveLength(1)
  })

  // --- addAgent ---

  it('addAgent creates agent with generated id and timestamp', () => {
    const store = useAgentsStore()
    const result = store.addAgent({ name: 'New Agent', role: 'Dev' })
    expect(result.id).toMatch(/^agent-/)
    expect(result.created_at).toBeTruthy()
    expect(result.is_template).toBe(false)
    expect(store.agents).toHaveLength(1)
  })

  it('addAgent preserves provided id and created_at', () => {
    const store = useAgentsStore()
    const result = store.addAgent({ id: 'my-id', created_at: '2024-01-01T00:00:00Z' })
    expect(result.id).toBe('my-id')
    expect(result.created_at).toBe('2024-01-01T00:00:00Z')
  })

  // --- updateAgent ---

  it('updateAgent updates existing agent and sets updated_at', () => {
    const store = useAgentsStore()
    const agent = store.addAgent(makeAgent({ name: 'Original' }))
    const updated = store.updateAgent(agent.id, { name: 'Updated' })
    expect(updated.name).toBe('Updated')
    expect(updated.updated_at).toBeTruthy()
  })

  it('updateAgent returns null for unknown id', () => {
    const store = useAgentsStore()
    const result = store.updateAgent('nonexistent', { name: 'X' })
    expect(result).toBeNull()
  })

  // --- removeAgent ---

  it('removeAgent removes agent by id', () => {
    const store = useAgentsStore()
    const agent = store.addAgent(makeAgent())
    store.removeAgent(agent.id)
    expect(store.agents).toHaveLength(0)
  })

  it('removeAgent is no-op for unknown id', () => {
    const store = useAgentsStore()
    store.addAgent(makeAgent())
    store.removeAgent('nonexistent')
    expect(store.agents).toHaveLength(1)
  })

  // --- cloneAgent ---

  it('cloneAgent clones an existing agent', () => {
    const store = useAgentsStore()
    const original = store.addAgent(makeAgent({ name: 'Original' }))
    const clone = store.cloneAgent(original.id)
    expect(clone).not.toBeNull()
    expect(clone.id).not.toBe(original.id)
    expect(clone.name).toBe('Original (Copy)')
    expect(clone.is_template).toBe(false)
    expect(store.agents).toHaveLength(2)
  })

  it('cloneAgent clones a template agent', () => {
    const store = useAgentsStore()
    const clone = store.cloneAgent('tmpl-vp-support')
    expect(clone).not.toBeNull()
    expect(clone.id).toMatch(/^agent-/)
    expect(clone.name).toBe('Jordan Rivera (Copy)')
    expect(clone.is_template).toBe(false)
    expect(store.agents).toHaveLength(1)
  })

  it('cloneAgent returns null for unknown id', () => {
    const store = useAgentsStore()
    const result = store.cloneAgent('nonexistent')
    expect(result).toBeNull()
  })

  // --- getAgent ---

  it('getAgent finds an agent in the agents list', () => {
    const store = useAgentsStore()
    const agent = store.addAgent(makeAgent({ name: 'Findable' }))
    expect(store.getAgent(agent.id).name).toBe('Findable')
  })

  it('getAgent finds a template agent', () => {
    const store = useAgentsStore()
    const found = store.getAgent('tmpl-cmo')
    expect(found).not.toBeNull()
    expect(found.name).toBe('Alex Kim')
  })

  it('getAgent returns null for unknown id', () => {
    const store = useAgentsStore()
    expect(store.getAgent('nonexistent')).toBeNull()
  })

  // --- clearAgents ---

  it('clearAgents empties the agents list', () => {
    const store = useAgentsStore()
    store.addAgent(makeAgent())
    store.addAgent(makeAgent())
    store.clearAgents()
    expect(store.agents).toEqual([])
  })

  // --- reset ---

  it('reset clears all state', () => {
    const store = useAgentsStore()
    store.addAgent(makeAgent())
    store.archetypes = [{ id: 'a1' }]
    store.loading = true
    store.error = 'some error'
    store.reset()
    expect(store.agents).toEqual([])
    expect(store.archetypes).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  // --- localStorage persistence ---

  it('loads stored agents from localStorage on init', () => {
    const stored = [{ id: 'stored-1', name: 'Stored Agent' }]
    localStorage.setItem(STORAGE_KEY, JSON.stringify(stored))
    setActivePinia(createPinia())
    const store = useAgentsStore()
    expect(store.agents).toHaveLength(1)
    expect(store.agents[0].id).toBe('stored-1')
  })

  it('saves agents to localStorage on change', async () => {
    const store = useAgentsStore()
    store.addAgent(makeAgent({ id: 'persist-1', name: 'Persisted' }))
    await vi.dynamicImportSettled()
    const raw = localStorage.getItem(STORAGE_KEY)
    const parsed = JSON.parse(raw)
    expect(parsed.some((a) => a.id === 'persist-1')).toBe(true)
  })

  it('handles corrupted localStorage gracefully', () => {
    localStorage.setItem(STORAGE_KEY, '{not-valid-json')
    setActivePinia(createPinia())
    const store = useAgentsStore()
    expect(store.agents).toEqual([])
  })

  it('handles non-array localStorage value', () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ not: 'an array' }))
    setActivePinia(createPinia())
    const store = useAgentsStore()
    expect(store.agents).toEqual([])
  })

  // --- fetchAgents (API) ---

  it('fetchAgents loads agents from API on success', async () => {
    agentsApi.list.mockResolvedValue({
      data: { data: [{ id: 'api-1', name: 'API Agent' }] },
    })
    const store = useAgentsStore()
    await store.fetchAgents()
    expect(store.agents).toHaveLength(1)
    expect(store.agents[0].id).toBe('api-1')
    expect(store.loading).toBe(false)
  })

  it('fetchAgents keeps localStorage agents when API fails', async () => {
    const stored = [{ id: 'local-1', name: 'Local' }]
    localStorage.setItem(STORAGE_KEY, JSON.stringify(stored))
    setActivePinia(createPinia())
    agentsApi.list.mockRejectedValue(new Error('Network error'))
    const store = useAgentsStore()
    await store.fetchAgents()
    expect(store.agents).toHaveLength(1)
    expect(store.agents[0].id).toBe('local-1')
    expect(store.loading).toBe(false)
  })

  it('fetchAgents ignores non-array API response', async () => {
    agentsApi.list.mockResolvedValue({ data: { data: 'not-an-array' } })
    const store = useAgentsStore()
    store.addAgent(makeAgent({ id: 'existing' }))
    await store.fetchAgents()
    expect(store.agents.some((a) => a.id === 'existing')).toBe(true)
  })

  // --- deleteAgent (API) ---

  it('deleteAgent removes agent from list on API success', async () => {
    agentsApi.delete.mockResolvedValue({})
    const store = useAgentsStore()
    store.addAgent(makeAgent({ id: 'del-1' }))
    const result = await store.deleteAgent('del-1')
    expect(result).toBe(true)
    expect(store.agents).toHaveLength(0)
    expect(store.loading).toBe(false)
  })

  it('deleteAgent sets error on API failure', async () => {
    agentsApi.delete.mockRejectedValue(new Error('Server error'))
    const store = useAgentsStore()
    store.addAgent(makeAgent({ id: 'del-1' }))
    const result = await store.deleteAgent('del-1')
    expect(result).toBe(false)
    expect(store.error).toBe('Server error')
    expect(store.agents).toHaveLength(1)
    expect(store.loading).toBe(false)
  })

  // --- generateAgent (API) ---

  it('generateAgent returns agent data on success', async () => {
    const agentData = { name: 'Generated', role: 'AI Agent' }
    agentsApi.generate.mockResolvedValue({ data: { data: agentData } })
    const store = useAgentsStore()
    const result = await store.generateAgent('Create a sales agent')
    expect(result).toEqual(agentData)
    expect(store.loading).toBe(false)
  })

  it('generateAgent returns null on API failure', async () => {
    agentsApi.generate.mockRejectedValue(new Error('LLM unavailable'))
    const store = useAgentsStore()
    const result = await store.generateAgent('test')
    expect(result).toBeNull()
    expect(store.error).toBe('LLM unavailable')
    expect(store.loading).toBe(false)
  })

  // --- fetchArchetypes (API) ---

  it('fetchArchetypes loads archetypes on success', async () => {
    agentsApi.listArchetypes.mockResolvedValue({
      data: { archetypes: [{ id: 'arch-1', category: 'buyer' }] },
    })
    const store = useAgentsStore()
    await store.fetchArchetypes()
    expect(store.archetypes).toHaveLength(1)
    expect(store.loading).toBe(false)
  })

  it('fetchArchetypes skips when archetypes already loaded', async () => {
    const store = useAgentsStore()
    store.archetypes = [{ id: 'existing' }]
    await store.fetchArchetypes()
    expect(agentsApi.listArchetypes).not.toHaveBeenCalled()
  })

  it('fetchArchetypes sets error on failure', async () => {
    agentsApi.listArchetypes.mockRejectedValue(new Error('Fetch failed'))
    const store = useAgentsStore()
    await store.fetchArchetypes()
    expect(store.error).toBe('Fetch failed')
    expect(store.loading).toBe(false)
  })

  // --- createAgentFromArchetype (API) ---

  it('createAgentFromArchetype adds agent to list on success', async () => {
    const newAgent = { id: 'created-1', name: 'From Archetype' }
    agentsApi.createFromArchetype.mockResolvedValue({ data: { agent: newAgent } })
    const store = useAgentsStore()
    const result = await store.createAgentFromArchetype({ archetype_id: 'arch-1' })
    expect(result).toEqual(newAgent)
    expect(store.agents).toHaveLength(1)
    expect(store.loading).toBe(false)
  })

  it('createAgentFromArchetype sets error and throws on failure', async () => {
    agentsApi.createFromArchetype.mockRejectedValue(new Error('Creation failed'))
    const store = useAgentsStore()
    await expect(store.createAgentFromArchetype({})).rejects.toThrow('Creation failed')
    expect(store.error).toBe('Creation failed')
    expect(store.loading).toBe(false)
  })

  // --- createBatch (API) ---

  it('createBatch adds agents to list on success', async () => {
    const agents = [{ id: 'b1' }, { id: 'b2' }]
    agentsApi.createBatch.mockResolvedValue({ data: { agents } })
    const store = useAgentsStore()
    const result = await store.createBatch({ buyer: 2 })
    expect(result).toHaveLength(2)
    expect(store.agents).toHaveLength(2)
    expect(store.loading).toBe(false)
  })

  it('createBatch sets error and throws on failure', async () => {
    agentsApi.createBatch.mockRejectedValue(new Error('Batch failed'))
    const store = useAgentsStore()
    await expect(store.createBatch({})).rejects.toThrow('Batch failed')
    expect(store.error).toBe('Batch failed')
    expect(store.loading).toBe(false)
  })

  // --- createFromScenario (API) ---

  it('createFromScenario adds agents to list on success', async () => {
    const agents = [{ id: 's1' }]
    agentsApi.createFromScenario.mockResolvedValue({ data: { agents } })
    const store = useAgentsStore()
    const result = await store.createFromScenario({ type: 'buyer' })
    expect(result).toHaveLength(1)
    expect(store.agents).toHaveLength(1)
    expect(store.loading).toBe(false)
  })

  it('createFromScenario sets error and throws on failure', async () => {
    agentsApi.createFromScenario.mockRejectedValue(new Error('Scenario failed'))
    const store = useAgentsStore()
    await expect(store.createFromScenario({})).rejects.toThrow('Scenario failed')
    expect(store.error).toBe('Scenario failed')
    expect(store.loading).toBe(false)
  })
})
