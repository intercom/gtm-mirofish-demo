import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { resolve } from 'path'

const css = readFileSync(resolve(__dirname, '../animations.css'), 'utf-8')

describe('animations.css', () => {
  it('defines all required animation classes', () => {
    expect(css).toContain('.animate-fade-in')
    expect(css).toContain('.animate-slide-up')
    expect(css).toContain('.animate-scale-in')
    expect(css).toContain('.animate-bounce')
  })

  it('uses CSS custom properties for configurable duration', () => {
    expect(css).toContain('--anim-duration')
  })

  it('uses CSS custom properties for configurable delay', () => {
    expect(css).toContain('--anim-delay')
  })

  it('respects prefers-reduced-motion', () => {
    expect(css).toContain('prefers-reduced-motion: reduce')
    expect(css).toContain('animation: none !important')
  })

  it('defines keyframes for each animation', () => {
    expect(css).toContain('@keyframes anim-fade-in')
    expect(css).toContain('@keyframes anim-slide-up')
    expect(css).toContain('@keyframes anim-scale-in')
    expect(css).toContain('@keyframes anim-bounce')
  })
})
