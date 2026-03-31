import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'

vi.mock('../../api/personas', () => ({
  personasApi: {
    generate: vi.fn(),
    list: vi.fn(),
    get: vi.fn(),
    update: vi.fn(),
    enhance: vi.fn(),
  },
}))

vi.mock('../../api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

import { usePersonasStore } from '../personas'
import { personasApi } from '../../api/personas'
import client from '../../api/client'

describe('usePersonasStore', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  // --- Initial state ---

  it('initialises with empty state', () => {
    const store = usePersonasStore()
    expect(store.personas).toEqual([])
    expect(store.loading).toBe(false)
    expect(store.generating).toBe(false)
    expect(store.error).toBeNull()
    expect(store.generationSource).toBeNull()
  })

  // --- Computed ---

  it('count returns number of personas', () => {
    const store = usePersonasStore()
    expect(store.count).toBe(0)
    store.personas = [{ id: '1' }, { id: '2' }]
    expect(store.count).toBe(2)
  })

  it('hasPersonas is false when empty', () => {
    const store = usePersonasStore()
    expect(store.hasPersonas).toBe(false)
  })

  it('hasPersonas is true when personas exist', () => {
    const store = usePersonasStore()
    store.personas = [{ id: '1' }]
    expect(store.hasPersonas).toBe(true)
  })

  it('byRole groups personas by title', () => {
    const store = usePersonasStore()
    store.personas = [
      { id: '1', title: 'Sales Rep' },
      { id: '2', title: 'Engineer' },
      { id: '3', title: 'Sales Rep' },
    ]
    const grouped = store.byRole
    expect(grouped['Sales Rep']).toHaveLength(2)
    expect(grouped['Engineer']).toHaveLength(1)
  })

  it('byRole uses Unknown for personas without title', () => {
    const store = usePersonasStore()
    store.personas = [{ id: '1' }]
    expect(store.byRole['Unknown']).toHaveLength(1)
  })

  // --- generate ---

  it('generate sets personas and generationSource on success', async () => {
    const mockPersonas = [
      { id: 'p1', title: 'SDR', name: 'Alice' },
      { id: 'p2', title: 'AE', name: 'Bob' },
    ]
    personasApi.generate.mockResolvedValue({
      data: { personas: mockPersonas, source: 'llm' },
    })

    const store = usePersonasStore()
    const result = await store.generate('outbound', 10)

    expect(personasApi.generate).toHaveBeenCalledWith({
      scenario: 'outbound',
      num_agents: 10,
    })
    expect(result).toEqual(mockPersonas)
    expect(store.personas).toEqual(mockPersonas)
    expect(store.generationSource).toBe('llm')
    expect(store.loading).toBe(false)
    expect(store.generating).toBe(false)
  })

  it('generate passes graphId when provided', async () => {
    personasApi.generate.mockResolvedValue({
      data: { personas: [], source: 'template' },
    })

    const store = usePersonasStore()
    await store.generate('pricing', 5, 'graph-123')

    expect(personasApi.generate).toHaveBeenCalledWith({
      scenario: 'pricing',
      num_agents: 5,
      graph_id: 'graph-123',
    })
  })

  it('generate defaults source to template when not returned', async () => {
    personasApi.generate.mockResolvedValue({
      data: { personas: [] },
    })

    const store = usePersonasStore()
    await store.generate('test')

    expect(store.generationSource).toBe('template')
  })

  it('generate sets error on failure and returns empty array', async () => {
    personasApi.generate.mockRejectedValue(new Error('Generation failed'))

    const store = usePersonasStore()
    const result = await store.generate('outbound')

    expect(result).toEqual([])
    expect(store.error).toBe('Generation failed')
    expect(store.loading).toBe(false)
    expect(store.generating).toBe(false)
  })

  it('generate defaults error message when e.message is empty', async () => {
    personasApi.generate.mockRejectedValue({ message: '' })

    const store = usePersonasStore()
    await store.generate('test')

    expect(store.error).toBe('Failed to generate personas')
  })

  // --- fetchAll ---

  it('fetchAll populates personas', async () => {
    const mockPersonas = [{ id: 'p1', title: 'PM' }]
    personasApi.list.mockResolvedValue({
      data: { personas: mockPersonas },
    })

    const store = usePersonasStore()
    const result = await store.fetchAll()

    expect(result).toEqual(mockPersonas)
    expect(store.personas).toEqual(mockPersonas)
    expect(store.loading).toBe(false)
  })

  it('fetchAll handles empty personas response', async () => {
    personasApi.list.mockResolvedValue({ data: {} })

    const store = usePersonasStore()
    const result = await store.fetchAll()

    expect(result).toEqual([])
    expect(store.personas).toEqual([])
  })

  it('fetchAll sets error on failure', async () => {
    personasApi.list.mockRejectedValue(new Error('Fetch failed'))

    const store = usePersonasStore()
    const result = await store.fetchAll()

    expect(result).toEqual([])
    expect(store.error).toBe('Fetch failed')
    expect(store.loading).toBe(false)
  })

  // --- clonePersona ---

  it('clonePersona adds cloned persona to list', async () => {
    const cloned = { id: 'p-clone', title: 'SDR', name: 'Clone of Alice' }
    client.post.mockResolvedValue({ data: { persona: cloned } })

    const store = usePersonasStore()
    store.personas = [{ id: 'p1', title: 'SDR', name: 'Alice' }]
    const result = await store.clonePersona('p1', { name: 'Clone of Alice' })

    expect(client.post).toHaveBeenCalledWith('/api/v1/personas/p1/clone', { name: 'Clone of Alice' })
    expect(result).toEqual(cloned)
    expect(store.personas).toHaveLength(2)
    expect(store.personas[1]).toEqual(cloned)
  })

  it('clonePersona falls back to res.data when persona field is missing', async () => {
    const cloned = { id: 'p-clone', title: 'AE' }
    client.post.mockResolvedValue({ data: cloned })

    const store = usePersonasStore()
    const result = await store.clonePersona('p1')

    expect(result).toEqual(cloned)
    expect(store.personas).toHaveLength(1)
  })

  it('clonePersona sets error on failure', async () => {
    client.post.mockRejectedValue(new Error('Clone failed'))

    const store = usePersonasStore()
    const result = await store.clonePersona('p1')

    expect(result).toBeNull()
    expect(store.error).toBe('Clone failed')
  })

  // --- clear ---

  it('clear resets personas, generationSource, and error', () => {
    const store = usePersonasStore()
    store.personas = [{ id: '1' }]
    store.generationSource = 'llm'
    store.error = 'some error'

    store.clear()

    expect(store.personas).toEqual([])
    expect(store.generationSource).toBeNull()
    expect(store.error).toBeNull()
  })
})
