import { ref, watch } from 'vue'
import { defineStore } from 'pinia'

const STORAGE_KEY = 'mirofish_nav_order'

const DEFAULT_NAV_LINKS = [
  { id: 'home', to: '/', label: 'Home', exact: true },
  { id: 'simulations', to: '/simulations', label: 'Simulations', exact: false, showActiveDot: true },
  { id: 'settings', to: '/settings', label: 'Settings', exact: false },
]

function loadNavLinks() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return DEFAULT_NAV_LINKS.map(l => ({ ...l }))
    const savedIds = JSON.parse(raw)
    if (!Array.isArray(savedIds) || savedIds.length !== DEFAULT_NAV_LINKS.length) {
      return DEFAULT_NAV_LINKS.map(l => ({ ...l }))
    }
    const ordered = savedIds
      .map(id => DEFAULT_NAV_LINKS.find(l => l.id === id))
      .filter(Boolean)
    if (ordered.length !== DEFAULT_NAV_LINKS.length) {
      return DEFAULT_NAV_LINKS.map(l => ({ ...l }))
    }
    return ordered.map(l => ({ ...l }))
  } catch {
    return DEFAULT_NAV_LINKS.map(l => ({ ...l }))
  }
}

export const useNavigationStore = defineStore('navigation', () => {
  const navLinks = ref(loadNavLinks())

  watch(navLinks, (links) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(links.map(l => l.id)))
    } catch { /* storage unavailable */ }
  }, { deep: true })

  function resetOrder() {
    navLinks.value = DEFAULT_NAV_LINKS.map(l => ({ ...l }))
  }

  return { navLinks, resetOrder }
})
