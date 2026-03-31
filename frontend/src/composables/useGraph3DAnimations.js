import * as THREE from 'three'

/**
 * Animation utilities for 3D graph visualizations.
 * Provides entrance effects, breathing pulses, edge particle flow,
 * star field backgrounds, and smooth position interpolation.
 */
export function useGraph3DAnimations() {
  const anims = new Map()
  const clock = new THREE.Clock()

  /** Run all active animations. Call once per render frame. */
  function tick() {
    const t = clock.getElapsedTime()
    for (const [id, fn] of anims) {
      if (!fn(t)) anims.delete(id)
    }
  }

  /** Scale an object from 0 to 1 with elastic overshoot. */
  function entrance(obj, delay = 0, duration = 0.7) {
    obj.scale.setScalar(0.001)
    const t0 = clock.getElapsedTime() + delay
    const id = Symbol()
    anims.set(id, (t) => {
      const p = (t - t0) / duration
      if (p < 0) return true
      if (p >= 1) { obj.scale.setScalar(1); return false }
      obj.scale.setScalar(Math.max(0.001, elasticOut(p)))
      return true
    })
    return id
  }

  /** Continuous breathing scale oscillation. */
  function pulse(obj, { speed = 1.5, amp = 0.06, phase = 0 } = {}) {
    const id = Symbol()
    anims.set(id, (t) => {
      obj.scale.setScalar(1 + Math.sin(t * speed + phase) * amp)
      return true
    })
    return id
  }

  /** Oscillate material opacity for glow halos. */
  function haloPulse(mat, { speed = 2, min = 0.04, max = 0.14, phase = 0 } = {}) {
    const id = Symbol()
    anims.set(id, (t) => {
      mat.opacity = min + (Math.sin(t * speed + phase) * 0.5 + 0.5) * (max - min)
      return true
    })
    return id
  }

  /** Smoothly interpolate an object's position with easeOutCubic. */
  function lerpTo(obj, target, { duration = 2, delay = 0 } = {}) {
    const from = obj.position.clone()
    const to = target instanceof THREE.Vector3
      ? target
      : new THREE.Vector3(target.x, target.y, target.z)
    const t0 = clock.getElapsedTime() + delay
    const id = Symbol()
    anims.set(id, (t) => {
      const p = (t - t0) / duration
      if (p < 0) return true
      if (p >= 1) { obj.position.copy(to); return false }
      obj.position.lerpVectors(from, to, easeOutCubic(p))
      return true
    })
    return id
  }

  /** Ambient star field that slowly rotates. Returns disposable handle. */
  function createStarField(scene, { count = 150, radius = 500, color = 0x4488ff, size = 0.8 } = {}) {
    const positions = new Float32Array(count * 3)
    for (let i = 0; i < count; i++) {
      const theta = Math.random() * Math.PI * 2
      const phi = Math.acos(2 * Math.random() - 1)
      const r = radius * (0.4 + Math.random() * 0.6)
      positions[i * 3] = Math.sin(phi) * Math.cos(theta) * r
      positions[i * 3 + 1] = Math.sin(phi) * Math.sin(theta) * r
      positions[i * 3 + 2] = Math.cos(phi) * r
    }
    const geo = new THREE.BufferGeometry()
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    const mat = new THREE.PointsMaterial({
      color, size, transparent: true, opacity: 0.25,
      blending: THREE.AdditiveBlending, depthWrite: false, sizeAttenuation: true,
    })
    const points = new THREE.Points(geo, mat)
    scene.add(points)
    const id = Symbol()
    anims.set(id, (t) => {
      points.rotation.y = t * 0.015
      return true
    })
    return {
      points, animId: id,
      dispose() { anims.delete(id); scene.remove(points); geo.dispose(); mat.dispose() },
    }
  }

  /** Particles flowing along graph edges. Returns disposable handle. */
  function createEdgeParticles(scene, getLinks, { count = 60, speed = 0.3, color = 0x2068ff, size = 1.5 } = {}) {
    const positions = new Float32Array(count * 3)
    const progress = new Float32Array(count)
    const linkIdx = new Uint16Array(count)
    for (let i = 0; i < count; i++) {
      progress[i] = Math.random()
      linkIdx[i] = Math.floor(Math.random() * 100)
    }
    const geo = new THREE.BufferGeometry()
    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    const mat = new THREE.PointsMaterial({
      color, size, transparent: true, opacity: 0.5,
      blending: THREE.AdditiveBlending, depthWrite: false, sizeAttenuation: true,
    })
    const points = new THREE.Points(geo, mat)
    scene.add(points)

    const id = Symbol()
    anims.set(id, () => {
      const links = getLinks()
      if (!links.length) return true
      for (let i = 0; i < count; i++) {
        progress[i] += speed * 0.008
        if (progress[i] > 1) {
          progress[i] = 0
          linkIdx[i] = Math.floor(Math.random() * links.length)
        }
        const link = links[linkIdx[i] % links.length]
        const src = link?.source
        const tgt = link?.target
        if (!src || !tgt) continue
        const sx = typeof src === 'object' ? (src.x || 0) : 0
        const sy = typeof src === 'object' ? (src.y || 0) : 0
        const sz = typeof src === 'object' ? (src.z || 0) : 0
        const tx = typeof tgt === 'object' ? (tgt.x || 0) : 0
        const ty = typeof tgt === 'object' ? (tgt.y || 0) : 0
        const tz = typeof tgt === 'object' ? (tgt.z || 0) : 0
        const p = progress[i]
        positions[i * 3] = sx + (tx - sx) * p
        positions[i * 3 + 1] = sy + (ty - sy) * p
        positions[i * 3 + 2] = sz + (tz - sz) * p
      }
      geo.attributes.position.needsUpdate = true
      return true
    })
    return {
      points, animId: id,
      dispose() { anims.delete(id); scene.remove(points); geo.dispose(); mat.dispose() },
    }
  }

  function stop(id) { anims.delete(id) }
  function stopAll() { anims.clear() }
  function dispose() { stopAll() }

  return {
    tick, entrance, pulse, haloPulse, lerpTo,
    createStarField, createEdgeParticles,
    stop, stopAll, dispose, clock,
  }
}

function elasticOut(x) {
  const c4 = (2 * Math.PI) / 3
  return x === 0 ? 0 : x === 1 ? 1
    : Math.pow(2, -10 * x) * Math.sin((x * 10 - 0.75) * c4) + 1
}

function easeOutCubic(x) {
  return 1 - Math.pow(1 - x, 3)
}
