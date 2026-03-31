/**
 * Animation utility library — shared entrance/exit animations
 * using the Web Animations API.
 *
 * Every function returns a native Animation object (or array for staggerChildren)
 * so callers can await `.finished`, call `.cancel()`, etc.
 *
 * When `prefers-reduced-motion: reduce` is active, duration is set to 0
 * so the element snaps to its final state without visual motion.
 */

const EASING = 'ease'
const EASING_OVERSHOOT = 'cubic-bezier(0.34, 1.56, 0.64, 1)'
const DEFAULT_DURATION = 300

function prefersReducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

function dur(ms) {
  return prefersReducedMotion() ? 0 : ms
}

// ── Fade ────────────────────────────────────────────────────────────────────

export function fadeIn(el, duration = DEFAULT_DURATION) {
  return el.animate(
    [{ opacity: 0 }, { opacity: 1 }],
    { duration: dur(duration), easing: EASING, fill: 'forwards' },
  )
}

export function fadeOut(el, duration = DEFAULT_DURATION) {
  return el.animate(
    [{ opacity: 1 }, { opacity: 0 }],
    { duration: dur(duration), easing: EASING, fill: 'forwards' },
  )
}

// ── Slide ───────────────────────────────────────────────────────────────────

const SLIDE_IN_OFFSETS = {
  up: [0, 16],
  down: [0, -16],
  left: [16, 0],
  right: [-16, 0],
}

const SLIDE_OUT_OFFSETS = {
  up: [0, -16],
  down: [0, 16],
  left: [-16, 0],
  right: [16, 0],
}

export function slideIn(el, direction = 'up', duration = DEFAULT_DURATION) {
  const [x, y] = SLIDE_IN_OFFSETS[direction] || SLIDE_IN_OFFSETS.up
  return el.animate(
    [
      { opacity: 0, transform: `translate(${x}px, ${y}px)` },
      { opacity: 1, transform: 'translate(0, 0)' },
    ],
    { duration: dur(duration), easing: EASING, fill: 'forwards' },
  )
}

export function slideOut(el, direction = 'up', duration = DEFAULT_DURATION) {
  const [x, y] = SLIDE_OUT_OFFSETS[direction] || SLIDE_OUT_OFFSETS.up
  return el.animate(
    [
      { opacity: 1, transform: 'translate(0, 0)' },
      { opacity: 0, transform: `translate(${x}px, ${y}px)` },
    ],
    { duration: dur(duration), easing: EASING, fill: 'forwards' },
  )
}

// ── Scale / Bounce ──────────────────────────────────────────────────────────

export function scaleIn(el, duration = DEFAULT_DURATION) {
  return el.animate(
    [
      { opacity: 0, transform: 'scale(0.85)' },
      { opacity: 1, transform: 'scale(1)' },
    ],
    { duration: dur(duration), easing: EASING_OVERSHOOT, fill: 'forwards' },
  )
}

export function bounceIn(el, duration = 500) {
  return el.animate(
    [
      { opacity: 0, transform: 'scale(0.3)', offset: 0 },
      { opacity: 1, transform: 'scale(1.05)', offset: 0.5 },
      { opacity: 1, transform: 'scale(0.95)', offset: 0.7 },
      { opacity: 1, transform: 'scale(1)', offset: 1 },
    ],
    { duration: dur(duration), easing: EASING_OVERSHOOT, fill: 'forwards' },
  )
}

// ── Stagger ─────────────────────────────────────────────────────────────────

export function staggerChildren(parent, delay = 50) {
  const reduced = prefersReducedMotion()
  return Array.from(parent.children).map((child, i) =>
    child.animate(
      [
        { opacity: 0, transform: 'translateY(12px)' },
        { opacity: 1, transform: 'translateY(0)' },
      ],
      {
        duration: reduced ? 0 : 300,
        easing: EASING,
        fill: 'both',
        delay: reduced ? 0 : i * delay,
      },
    ),
  )
}
