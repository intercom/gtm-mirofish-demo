import { vi } from 'vitest'

export const mockObserve = vi.fn()
export const mockDisconnect = vi.fn()

export class MockResizeObserver {
  observe = mockObserve
  disconnect = mockDisconnect
  unobserve = vi.fn()
}

export function setupChartTests() {
  vi.stubGlobal('ResizeObserver', MockResizeObserver)
  mockSVGMethods()
}

export function cleanupChartTests() {
  vi.unstubAllGlobals()
  mockObserve.mockClear()
  mockDisconnect.mockClear()
}

function mockSVGMethods() {
  // D3 calls getTotalLength on SVG paths and getComputedTextLength on text
  // elements — these aren't implemented in happy-dom
  for (const cls of ['SVGElement', 'SVGGeometryElement', 'SVGTextContentElement', 'Element']) {
    const proto = globalThis[cls]?.prototype
    if (!proto) continue
    if (!proto.getTotalLength) proto.getTotalLength = () => 100
    if (!proto.getComputedTextLength) proto.getComputedTextLength = () => 50
  }
}

export function setDimensions(el, width = 600, height = 400) {
  if (!el) return
  Object.defineProperty(el, 'clientWidth', { value: width, configurable: true })
  Object.defineProperty(el, 'clientHeight', { value: height, configurable: true })
}
