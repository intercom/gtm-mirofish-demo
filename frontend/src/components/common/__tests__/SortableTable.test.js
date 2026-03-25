import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import SortableTable from '../SortableTable.vue'

const columns = [
  { key: 'name', label: 'Name', sortable: true },
  { key: 'score', label: 'Score', sortable: true, align: 'right' },
  { key: 'role', label: 'Role' },
]

const rows = [
  { id: 1, name: 'Charlie', score: 85, role: 'Dev' },
  { id: 2, name: 'Alice', score: 92, role: 'PM' },
  { id: 3, name: 'Bob', score: 78, role: 'Design' },
]

function factory(props = {}, opts = {}) {
  return mount(SortableTable, {
    props: { columns, rows, ...props },
    ...opts,
  })
}

describe('SortableTable', () => {
  it('renders all column headers', () => {
    const wrapper = factory()
    const headers = wrapper.findAll('th')
    expect(headers).toHaveLength(3)
    expect(headers[0].text()).toBe('Name')
    expect(headers[1].text()).toBe('Score')
    expect(headers[2].text()).toBe('Role')
  })

  it('renders all rows', () => {
    const wrapper = factory()
    const trs = wrapper.findAll('tbody tr')
    expect(trs).toHaveLength(3)
  })

  it('renders cell values', () => {
    const wrapper = factory()
    const cells = wrapper.findAll('tbody td')
    expect(cells[0].text()).toBe('Charlie')
    expect(cells[1].text()).toBe('85')
    expect(cells[2].text()).toBe('Dev')
  })

  it('sorts ascending on header click', async () => {
    const wrapper = factory()
    await wrapper.findAll('th')[0].trigger('click')
    const names = wrapper.findAll('tbody tr').map(tr => tr.findAll('td')[0].text())
    expect(names).toEqual(['Alice', 'Bob', 'Charlie'])
  })

  it('sorts descending on second click', async () => {
    const wrapper = factory()
    const header = wrapper.findAll('th')[0]
    await header.trigger('click')
    await header.trigger('click')
    const names = wrapper.findAll('tbody tr').map(tr => tr.findAll('td')[0].text())
    expect(names).toEqual(['Charlie', 'Bob', 'Alice'])
  })

  it('emits sort event on header click', async () => {
    const wrapper = factory()
    await wrapper.findAll('th')[0].trigger('click')
    expect(wrapper.emitted('sort')).toBeTruthy()
    expect(wrapper.emitted('sort')[0][0]).toEqual({ column: 'name', direction: 'asc' })
  })

  it('does not sort on non-sortable column click', async () => {
    const wrapper = factory()
    await wrapper.findAll('th')[2].trigger('click')
    expect(wrapper.emitted('sort')).toBeFalsy()
    const names = wrapper.findAll('tbody tr').map(tr => tr.findAll('td')[0].text())
    expect(names).toEqual(['Charlie', 'Alice', 'Bob'])
  })

  it('shows empty text when no rows', () => {
    const wrapper = factory({ rows: [], emptyText: 'Nothing here' })
    expect(wrapper.text()).toContain('Nothing here')
  })

  it('renders drag handles when draggable', () => {
    const wrapper = factory({ draggable: true })
    const headers = wrapper.findAll('th')
    expect(headers).toHaveLength(4)
    const handleCells = wrapper.findAll('tbody tr').map(tr => tr.findAll('td')[0])
    expect(handleCells).toHaveLength(3)
    handleCells.forEach(cell => {
      expect(cell.find('svg').exists()).toBe(true)
    })
  })

  it('does not render drag handles when not draggable', () => {
    const wrapper = factory({ draggable: false })
    expect(wrapper.findAll('th')).toHaveLength(3)
  })

  it('renders striped rows', () => {
    const wrapper = factory({ striped: true })
    const secondRow = wrapper.findAll('tbody tr')[1]
    expect(secondRow.classes()).toContain('bg-[var(--color-tint)]')
  })

  it('supports custom cell slots', () => {
    const wrapper = factory({}, {
      slots: {
        'cell-name': ({ value }) => `Custom: ${value}`,
      },
    })
    const firstCell = wrapper.findAll('tbody td')[0]
    expect(firstCell.text()).toBe('Custom: Charlie')
  })

  it('applies right alignment class', () => {
    const wrapper = factory()
    const scoreHeader = wrapper.findAll('th')[1]
    expect(scoreHeader.classes()).toContain('text-right')
    const scoreCell = wrapper.findAll('tbody tr')[0].findAll('td')[1]
    expect(scoreCell.classes()).toContain('text-right')
  })
})
