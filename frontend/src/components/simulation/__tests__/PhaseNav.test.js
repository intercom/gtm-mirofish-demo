import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import PhaseNav from '../PhaseNav.vue'

function mountNav(props = {}) {
  return mount(PhaseNav, {
    props: { taskId: 'task-abc', activePhase: 'graph', ...props },
    global: {
      stubs: { RouterLink: { template: '<a :to="to"><slot /></a>', props: ['to'] } },
    },
  })
}

describe('PhaseNav', () => {
  it('renders all three phase tabs', () => {
    const wrapper = mountNav()
    expect(wrapper.text()).toContain('Graph')
    expect(wrapper.text()).toContain('Simulation')
    expect(wrapper.text()).toContain('Report')
  })

  it('generates correct route for each phase', () => {
    const wrapper = mountNav({ taskId: 'xyz-123' })
    const links = wrapper.findAll('a')
    expect(links[0].attributes('to')).toBe('/workspace/xyz-123?tab=graph')
    expect(links[1].attributes('to')).toBe('/workspace/xyz-123?tab=simulation')
    expect(links[2].attributes('to')).toBe('/report/xyz-123')
  })

  it('applies active styling to the current phase', () => {
    const wrapper = mountNav({ activePhase: 'simulation' })
    const links = wrapper.findAll('a')
    expect(links[1].classes()).toContain('border-[var(--color-primary)]')
    expect(links[0].classes()).toContain('border-transparent')
  })

  it('renders an SVG icon for each phase', () => {
    const wrapper = mountNav()
    const svgs = wrapper.findAll('svg')
    expect(svgs).toHaveLength(3)
  })

  it('renders graph icon with circles and lines', () => {
    const wrapper = mountNav({ activePhase: 'graph' })
    const graphSvg = wrapper.findAll('svg')[0]
    expect(graphSvg.findAll('circle')).toHaveLength(3)
    expect(graphSvg.findAll('line')).toHaveLength(3)
  })

  it('renders simulation icon with play triangle path', () => {
    const wrapper = mountNav()
    const simSvg = wrapper.findAll('svg')[1]
    expect(simSvg.find('path').exists()).toBe(true)
    expect(simSvg.attributes('fill')).toBe('currentColor')
  })

  it('renders report icon with rect and lines', () => {
    const wrapper = mountNav()
    const reportSvg = wrapper.findAll('svg')[2]
    expect(reportSvg.find('rect').exists()).toBe(true)
    expect(reportSvg.findAll('line').length).toBeGreaterThanOrEqual(3)
  })
})
