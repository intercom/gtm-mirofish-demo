import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { ref } from 'vue'
import WorkspacePhaseNav from '../WorkspacePhaseNav.vue'

function makePolling(overrides = {}) {
  return {
    graphData: ref(overrides.graphData ?? { nodes: [] }),
    graphStatus: ref(overrides.graphStatus ?? 'idle'),
    graphProgress: ref(overrides.graphProgress ?? 0),
    runStatus: ref(overrides.runStatus ?? null),
    simStatus: ref(overrides.simStatus ?? 'idle'),
  }
}

function mountNav(props = {}, pollingOverrides = {}) {
  return mount(WorkspacePhaseNav, {
    props: {
      activeTab: 'graph',
      taskId: 'task-1',
      polling: makePolling(pollingOverrides),
      ...props,
    },
    global: {
      stubs: { RouterLink: { template: '<a :to="to"><slot /></a>', props: ['to'] } },
    },
  })
}

describe('WorkspacePhaseNav', () => {
  it('renders Graph and Simulation tabs', () => {
    const wrapper = mountNav()
    const buttons = wrapper.findAll('button')
    expect(buttons).toHaveLength(2)
    expect(buttons[0].text()).toContain('Graph')
    expect(buttons[1].text()).toContain('Simulation')
  })

  it('highlights the active tab', () => {
    const wrapper = mountNav({ activeTab: 'simulation' })
    const simButton = wrapper.findAll('button')[1]
    expect(simButton.classes()).toContain("text-[#050505]")
  })

  it('emits update:activeTab when a tab is clicked', async () => {
    const wrapper = mountNav({ activeTab: 'graph' })
    await wrapper.findAll('button')[1].trigger('click')
    expect(wrapper.emitted('update:activeTab')).toBeTruthy()
    expect(wrapper.emitted('update:activeTab')[0]).toEqual(['simulation'])
  })

  it('shows active indicator bar under active tab', () => {
    const wrapper = mountNav({ activeTab: 'graph' })
    const graphButton = wrapper.findAll('button')[0]
    const indicator = graphButton.find('.bg-\\[\\#2068FF\\]')
    expect(indicator.exists()).toBe(true)
  })

  it('shows node count metric when graph has nodes', () => {
    const wrapper = mountNav({}, { graphData: { nodes: new Array(42) } })
    expect(wrapper.text()).toContain('42 nodes')
  })

  it('hides node count metric when graph is empty', () => {
    const wrapper = mountNav({}, { graphData: { nodes: [] } })
    expect(wrapper.text()).not.toContain('nodes')
  })

  it('shows round metric when simulation is running', () => {
    const wrapper = mountNav({}, {
      simStatus: 'running',
      runStatus: { current_round: 5, total_rounds: 24 },
    })
    expect(wrapper.text()).toContain('Round 5/24')
  })

  it('shows (Complete) metric when simulation is completed', () => {
    const wrapper = mountNav({}, { simStatus: 'completed' })
    expect(wrapper.text()).toContain('(Complete)')
  })

  it('shows no sim metric when idle', () => {
    const wrapper = mountNav({}, { simStatus: 'idle' })
    expect(wrapper.text()).not.toContain('Round')
    expect(wrapper.text()).not.toContain('(Complete)')
  })

  it('shows building spinner when graph is building', () => {
    const wrapper = mountNav({}, { graphStatus: 'building', graphProgress: 45 })
    expect(wrapper.find('.animate-spin').exists()).toBe(true)
    expect(wrapper.text()).toContain('Building graph... 45%')
  })

  it('shows running pulse indicator when simulation is running', () => {
    const wrapper = mountNav({}, { simStatus: 'running' })
    expect(wrapper.find('.animate-pulse').exists()).toBe(true)
    expect(wrapper.text()).toContain('Running simulation...')
  })

  it('shows complete text when simulation is completed', () => {
    const wrapper = mountNav({}, { simStatus: 'completed' })
    expect(wrapper.text()).toContain('Complete')
  })

  it('shows report link when simulation is completed', () => {
    const wrapper = mountNav({ taskId: 'task-99' }, { simStatus: 'completed' })
    const reportLink = wrapper.find('a')
    expect(reportLink.exists()).toBe(true)
    expect(reportLink.attributes('to')).toBe('/report/task-99')
  })

  it('hides report link when simulation is not completed', () => {
    const wrapper = mountNav({}, { simStatus: 'running' })
    expect(wrapper.find('a').exists()).toBe(false)
  })
})
