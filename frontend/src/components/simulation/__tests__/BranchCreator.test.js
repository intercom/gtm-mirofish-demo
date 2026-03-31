import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { nextTick } from 'vue'
import BranchCreator from '../BranchCreator.vue'

const stubs = {
  AppButton: {
    template: '<button :disabled="disabled"><slot /></button>',
    props: ['disabled', 'loading', 'variant', 'size'],
  },
  AppInput: {
    template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" :placeholder="placeholder" />',
    props: ['modelValue', 'placeholder', 'type', 'options'],
    emits: ['update:modelValue'],
  },
  AppBadge: {
    template: '<span><slot /></span>',
    props: ['variant'],
  },
}

function mountCreator(props = {}) {
  return mount(BranchCreator, {
    props: {
      simulationId: 'sim-001',
      totalRounds: 24,
      currentRound: 12,
      ...props,
    },
    global: { stubs },
  })
}

async function fillForm(wrapper) {
  const completedMarker = wrapper.findAll('.flex.flex-col.items-center.cursor-pointer').find(el => {
    const dot = el.find('div')
    return dot.exists() && !dot.classes().some(c => c.includes('cursor-not-allowed'))
  })
  await completedMarker.trigger('click')
  await nextTick()

  const inputs = wrapper.findAll('input')
  const modValueInput = inputs[1]
  await modValueInput.setValue('A competitor launches a product')
  const addBtn = wrapper.findAll('button').find(b => b.text() === 'Add')
  await addBtn.trigger('click')
  await nextTick()

  const labelInput = inputs[2]
  await labelInput.setValue('Test branch')
  await nextTick()
}

describe('BranchCreator', () => {
  it('renders "Create Branch" heading', () => {
    const wrapper = mountCreator()
    expect(wrapper.find('h2').text()).toBe('Create Branch')
  })

  it('shows all 3 step headers', () => {
    const wrapper = mountCreator()
    expect(wrapper.text()).toContain('Select Branch Point')
    expect(wrapper.text()).toContain('Define Modifications')
    expect(wrapper.text()).toContain('Name Your Branch')
  })

  it('shows round markers on timeline', () => {
    const wrapper = mountCreator({ totalRounds: 24, currentRound: 12 })
    expect(wrapper.text()).toContain('R1')
  })

  it('completed rounds are clickable', () => {
    const wrapper = mountCreator({ totalRounds: 24, currentRound: 12 })
    const markers = wrapper.findAll('.flex.flex-col.items-center.cursor-pointer')
    const completedMarker = markers[0]
    const dot = completedMarker.find('div')
    expect(dot.classes().some(c => c.includes('cursor-not-allowed'))).toBe(false)
  })

  it('uncompleted rounds are visually disabled', () => {
    const wrapper = mountCreator({ totalRounds: 24, currentRound: 6 })
    const markers = wrapper.findAll('.flex.flex-col.items-center.cursor-pointer')
    const lastMarker = markers[markers.length - 1]
    const dot = lastMarker.find('div')
    expect(dot.classes().some(c => c.includes('cursor-not-allowed') || c.includes('opacity-40'))).toBe(true)
  })

  it('selecting a round shows "Round N selected" badge', async () => {
    const wrapper = mountCreator({ totalRounds: 24, currentRound: 12 })
    const markers = wrapper.findAll('.flex.flex-col.items-center.cursor-pointer')
    await markers[0].trigger('click')
    await nextTick()
    expect(wrapper.text()).toContain('Round 1')
    expect(wrapper.text()).toContain('selected as branch point')
  })

  it('shows empty modifications state', () => {
    const wrapper = mountCreator()
    expect(wrapper.text()).toContain('No modifications added yet')
  })

  it('adds modification to list', async () => {
    const wrapper = mountCreator()
    const inputs = wrapper.findAll('input')
    const modValueInput = inputs[1]
    await modValueInput.setValue('A competitor launches a product')
    const addBtn = wrapper.findAll('button').find(b => b.text() === 'Add')
    await addBtn.trigger('click')
    await nextTick()
    expect(wrapper.text()).toContain('A competitor launches a product')
    expect(wrapper.text()).toContain('Inject event')
  })

  it('removes modification from list', async () => {
    const wrapper = mountCreator()
    const inputs = wrapper.findAll('input')
    await inputs[1].setValue('Some event')
    const addBtn = wrapper.findAll('button').find(b => b.text() === 'Add')
    await addBtn.trigger('click')
    await nextTick()
    expect(wrapper.text()).toContain('Some event')

    const modItem = wrapper.find('.bg-\\[var\\(--color-tint\\)\\].rounded-lg')
    const removeBtn = modItem.find('button')
    await removeBtn.trigger('click')
    await nextTick()
    expect(wrapper.text()).not.toContain('Some event')
    expect(wrapper.text()).toContain('No modifications added yet')
  })

  it('shows modification type label and value', async () => {
    const wrapper = mountCreator()
    const inputs = wrapper.findAll('input')
    await inputs[1].setValue('Finance analyst at a hedge fund')
    const addBtn = wrapper.findAll('button').find(b => b.text() === 'Add')
    await addBtn.trigger('click')
    await nextTick()
    expect(wrapper.text()).toContain('Inject event')
    expect(wrapper.text()).toContain('Finance analyst at a hedge fund')
  })

  it('create button disabled when nothing filled', () => {
    const wrapper = mountCreator()
    const createBtn = wrapper.findAll('button').find(b => b.text() === 'Create Branch')
    expect(createBtn.attributes('disabled')).toBeDefined()
  })

  it('create button disabled when only round selected', async () => {
    const wrapper = mountCreator({ currentRound: 12 })
    const markers = wrapper.findAll('.flex.flex-col.items-center.cursor-pointer')
    await markers[0].trigger('click')
    await nextTick()
    const createBtn = wrapper.findAll('button').find(b => b.text() === 'Create Branch')
    expect(createBtn.attributes('disabled')).toBeDefined()
  })

  it('create button disabled when no modifications', async () => {
    const wrapper = mountCreator({ currentRound: 12 })
    const markers = wrapper.findAll('.flex.flex-col.items-center.cursor-pointer')
    await markers[0].trigger('click')
    await nextTick()
    const inputs = wrapper.findAll('input')
    await inputs[2].setValue('My branch')
    await nextTick()
    const createBtn = wrapper.findAll('button').find(b => b.text() === 'Create Branch')
    expect(createBtn.attributes('disabled')).toBeDefined()
  })

  it('create button enabled when all 3 steps complete', async () => {
    const wrapper = mountCreator({ currentRound: 12 })
    await fillForm(wrapper)
    const createBtn = wrapper.findAll('button').find(b => b.text() === 'Create Branch')
    expect(createBtn.attributes('disabled')).toBeUndefined()
  })

  it('emits branch-created with correct payload on create', async () => {
    const wrapper = mountCreator({ currentRound: 12 })
    const markers = wrapper.findAll('.flex.flex-col.items-center.cursor-pointer')
    await markers[0].trigger('click')
    await nextTick()

    const inputs = wrapper.findAll('input')
    await inputs[1].setValue('New competitor enters market')
    const addBtn = wrapper.findAll('button').find(b => b.text() === 'Add')
    await addBtn.trigger('click')
    await nextTick()

    await inputs[2].setValue('Competitor branch')
    await nextTick()

    const createBtn = wrapper.findAll('button').find(b => b.text() === 'Create Branch')
    await createBtn.trigger('click')
    await nextTick()

    expect(wrapper.emitted('branch-created')).toHaveLength(1)
    const payload = wrapper.emitted('branch-created')[0][0]
    expect(payload.simulationId).toBe('sim-001')
    expect(payload.at_round).toBe(1)
    expect(payload.label).toBe('Competitor branch')
    expect(payload.modifications).toHaveLength(1)
    expect(payload.modifications[0].type).toBe('inject_event')
    expect(payload.modifications[0].value).toBe('New competitor enters market')
  })

  it('emits cancel on cancel click', async () => {
    const wrapper = mountCreator()
    const cancelBtn = wrapper.findAll('button').find(b => b.text() === 'Cancel')
    await cancelBtn.trigger('click')
    expect(wrapper.emitted('cancel')).toHaveLength(1)
  })

  it('reset clears all form state', async () => {
    const wrapper = mountCreator({ currentRound: 12 })
    await fillForm(wrapper)
    expect(wrapper.text()).toContain('selected as branch point')

    const resetBtn = wrapper.findAll('button').find(b => b.text() === 'Reset')
    await resetBtn.trigger('click')
    await nextTick()

    expect(wrapper.text()).toContain('No modifications added yet')
    expect(wrapper.text()).not.toContain('selected as branch point')
  })

  it('shows preview text after configuring', async () => {
    const wrapper = mountCreator({ currentRound: 12 })
    const markers = wrapper.findAll('.flex.flex-col.items-center.cursor-pointer')
    await markers[0].trigger('click')
    await nextTick()
    expect(wrapper.text()).toContain('Branch from Round 1')
    expect(wrapper.text()).toContain('No modifications added yet')
  })
})
