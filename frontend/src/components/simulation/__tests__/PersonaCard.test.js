import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import PersonaCard from '../PersonaCard.vue'

function mountCard(props = {}) {
  return mount(PersonaCard, {
    props: { ...props },
  })
}

describe('PersonaCard', () => {
  describe('name parsing', () => {
    it('renders name from name prop directly', () => {
      const wrapper = mountCard({ name: 'Alice' })
      expect(wrapper.text()).toContain('Alice')
    })

    it('parses fullName "Alice, VP Sales @ Intercom" correctly', () => {
      const wrapper = mountCard({ fullName: 'Alice, VP Sales @ Intercom' })
      expect(wrapper.text()).toContain('Alice')
      expect(wrapper.text()).toContain('VP Sales')
      expect(wrapper.text()).toContain('Intercom')
    })

    it('parses fullName "Bob (Engineer@Corp)" format', () => {
      const wrapper = mountCard({ fullName: 'Bob (Engineer@Corp)' })
      expect(wrapper.text()).toContain('Bob')
      expect(wrapper.text()).toContain('Engineer')
      expect(wrapper.text()).toContain('Corp')
    })
  })

  describe('avatar', () => {
    it('shows initial letter avatar', () => {
      const wrapper = mountCard({ name: 'Zara' })
      const avatar = wrapper.find('.rounded-full.text-white')
      expect(avatar.text()).toBe('Z')
    })

    it('avatar color is deterministic for same name', () => {
      const a = mountCard({ name: 'Alice' })
      const b = mountCard({ name: 'Alice' })
      const colorA = a.find('.rounded-full.text-white').attributes('style')
      const colorB = b.find('.rounded-full.text-white').attributes('style')
      expect(colorA).toBe(colorB)
    })
  })

  describe('role and company', () => {
    it('shows role and company when provided', () => {
      const wrapper = mountCard({ name: 'Alice', role: 'VP Sales', company: 'Intercom' })
      expect(wrapper.text()).toContain('VP Sales')
      expect(wrapper.text()).toContain('Intercom')
    })

    it('hides role/company line when both empty', () => {
      const wrapper = mountCard({ name: 'Alice', role: '', company: '' })
      const subtitle = wrapper.find('p')
      expect(subtitle.exists()).toBe(false)
    })
  })

  describe('sentiment badge', () => {
    it('shows sentiment badge with correct label', () => {
      const wrapper = mountCard({ name: 'Alice', sentiment: 'positive' })
      expect(wrapper.text()).toContain('positive')
    })

    it('maps "positive" sentiment correctly', () => {
      const wrapper = mountCard({ name: 'Alice', sentiment: 'positive' })
      const badge = wrapper.find('.rounded-full.text-\\[10px\\]')
      expect(badge.attributes('style')).toContain('var(--color-success)')
    })

    it('maps "skeptical" sentiment correctly', () => {
      const wrapper = mountCard({ name: 'Alice', sentiment: 'skeptical' })
      const badge = wrapper.find('.rounded-full.text-\\[10px\\]')
      expect(badge.attributes('style')).toContain('var(--color-warning)')
    })
  })

  describe('stats bar', () => {
    it('shows "actions" stat text when totalActions > 0', () => {
      const wrapper = mountCard({ name: 'Alice', totalActions: 10 })
      expect(wrapper.text()).toContain('10 actions')
    })

    it('hides stats bar in compact mode even with totalActions', () => {
      const wrapper = mountCard({ name: 'Alice', totalActions: 10, compact: true })
      expect(wrapper.text()).not.toContain('actions')
      expect(wrapper.findAll('.grid').length).toBe(0)
    })
  })

  describe('clickable behavior', () => {
    it('renders as button when clickable', () => {
      const wrapper = mountCard({ name: 'Alice', clickable: true })
      expect(wrapper.element.tagName).toBe('BUTTON')
    })

    it('renders as div when not clickable', () => {
      const wrapper = mountCard({ name: 'Alice', clickable: false })
      expect(wrapper.element.tagName).toBe('DIV')
    })

    it('emits click when clickable button is clicked', async () => {
      const wrapper = mountCard({ name: 'Alice', clickable: true })
      await wrapper.trigger('click')
      expect(wrapper.emitted('click')).toHaveLength(1)
    })
  })

  describe('removable behavior', () => {
    it('shows remove button when removable', () => {
      const wrapper = mountCard({ name: 'Alice', removable: true })
      const removeBtn = wrapper.find('button[title="Remove from team"]')
      expect(removeBtn.exists()).toBe(true)
    })

    it('emits remove on remove button click', async () => {
      const wrapper = mountCard({ name: 'Alice', removable: true })
      const removeBtn = wrapper.find('button[title="Remove from team"]')
      await removeBtn.trigger('click')
      expect(wrapper.emitted('remove')).toHaveLength(1)
    })

    it('does not emit click when remove button is clicked (stop propagation)', async () => {
      const wrapper = mountCard({ name: 'Alice', clickable: true, removable: true })
      const removeBtn = wrapper.find('button[title="Remove from team"]')
      await removeBtn.trigger('click')
      expect(wrapper.emitted('remove')).toHaveLength(1)
      expect(wrapper.emitted('click')).toBeUndefined()
    })
  })
})
