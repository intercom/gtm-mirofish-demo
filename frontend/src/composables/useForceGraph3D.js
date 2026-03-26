import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'

const ALPHA_DECAY = 0.028
const ALPHA_MIN = 0.001
const VELOCITY_DECAY = 0.4
const CHARGE_STRENGTH = -200
const LINK_DISTANCE = 80
const LINK_STRENGTH = 0.03
const CENTER_STRENGTH = 0.005

export function useForceGraph3D({ onNodeClick, onNodeHover } = {}) {
  let container = null
  let renderer = null
  let scene = null
  let camera = null
  let controls = null
  let animFrameId = null
  let resizeObserver = null

  const raycaster = new THREE.Raycaster()
  const pointer = new THREE.Vector2(-999, -999)

  let nodeGroup = null
  let edgeLine = null
  let edgePositions = null
  let simNodes = []
  let simLinks = []
  let alpha = 1.0
  let prevHoveredMesh = null

  function init(el) {
    container = el
    const w = el.clientWidth || 800
    const h = el.clientHeight || 600
    const isDark = document.documentElement.classList.contains('dark')
    const bgColor = isDark ? 0x0a0a1a : 0xf8f9fa

    scene = new THREE.Scene()
    scene.background = new THREE.Color(bgColor)
    scene.fog = new THREE.FogExp2(bgColor, 0.0015)

    camera = new THREE.PerspectiveCamera(60, w / h, 1, 2000)
    camera.position.set(0, 60, 220)

    renderer = new THREE.WebGLRenderer({ antialias: true })
    renderer.setSize(w, h)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    el.appendChild(renderer.domElement)

    controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.dampingFactor = 0.1
    controls.minDistance = 50
    controls.maxDistance = 800
    controls.autoRotate = true
    controls.autoRotateSpeed = 0.4

    scene.add(new THREE.AmbientLight(0xffffff, 0.6))
    const dir = new THREE.DirectionalLight(0xffffff, 0.8)
    dir.position.set(200, 200, 200)
    scene.add(dir)
    const fill = new THREE.DirectionalLight(0x4488ff, 0.3)
    fill.position.set(-100, -50, -100)
    scene.add(fill)

    nodeGroup = new THREE.Group()
    scene.add(nodeGroup)

    renderer.domElement.addEventListener('pointermove', handlePointerMove)
    renderer.domElement.addEventListener('click', handleClick)

    resizeObserver = new ResizeObserver(handleResize)
    resizeObserver.observe(el)

    animate()
  }

  function setData(nodes, edges) {
    clearObjects()

    simNodes = nodes.map((n) => {
      const phi = Math.random() * Math.PI * 2
      const theta = Math.acos(2 * Math.random() - 1)
      const r = 30 + Math.random() * 80

      const x = Math.sin(theta) * Math.cos(phi) * r
      const y = Math.sin(theta) * Math.sin(phi) * r
      const z = Math.cos(theta) * r

      const geo = new THREE.SphereGeometry(n.radius, 20, 14)
      const mat = new THREE.MeshPhongMaterial({
        color: new THREE.Color(n.color),
        emissive: new THREE.Color(n.color),
        emissiveIntensity: 0.3,
        shininess: 60,
        transparent: true,
        opacity: 0.92,
      })
      const mesh = new THREE.Mesh(geo, mat)
      mesh.position.set(x, y, z)
      mesh.userData = { nodeId: n.id, nodeData: n }

      const haloGeo = new THREE.SphereGeometry(n.radius * 1.8, 12, 8)
      const haloMat = new THREE.MeshBasicMaterial({
        color: new THREE.Color(n.color),
        transparent: true,
        opacity: 0.07,
      })
      mesh.add(new THREE.Mesh(haloGeo, haloMat))

      nodeGroup.add(mesh)
      return { id: n.id, x, y, z, vx: 0, vy: 0, vz: 0, mesh, data: n }
    })

    const nodeMap = new Map(simNodes.map(n => [n.id, n]))

    simLinks = edges
      .filter(e => nodeMap.has(e.sourceId) && nodeMap.has(e.targetId))
      .map(e => ({
        source: nodeMap.get(e.sourceId),
        target: nodeMap.get(e.targetId),
        data: e,
      }))

    edgePositions = new Float32Array(simLinks.length * 6)
    const geo = new THREE.BufferGeometry()
    geo.setAttribute('position', new THREE.BufferAttribute(edgePositions, 3))

    const isDark = document.documentElement.classList.contains('dark')
    const mat = new THREE.LineBasicMaterial({
      color: isDark ? 0x4488ff : 0x2068ff,
      transparent: true,
      opacity: isDark ? 0.18 : 0.14,
    })
    edgeLine = new THREE.LineSegments(geo, mat)
    scene.add(edgeLine)

    alpha = 1.0
  }

  function clearObjects() {
    if (nodeGroup) {
      while (nodeGroup.children.length) {
        const child = nodeGroup.children[0]
        child.traverse(obj => {
          obj.geometry?.dispose()
          if (obj.material) {
            if (Array.isArray(obj.material)) obj.material.forEach(m => m.dispose())
            else obj.material.dispose()
          }
        })
        nodeGroup.remove(child)
      }
    }
    if (edgeLine) {
      edgeLine.geometry?.dispose()
      edgeLine.material?.dispose()
      scene?.remove(edgeLine)
      edgeLine = null
    }
    simNodes = []
    simLinks = []
    edgePositions = null
    prevHoveredMesh = null
  }

  function simulationTick() {
    if (alpha < ALPHA_MIN || !simNodes.length) return

    for (let i = 0; i < simNodes.length; i++) {
      for (let j = i + 1; j < simNodes.length; j++) {
        const a = simNodes[i], b = simNodes[j]
        const dx = b.x - a.x, dy = b.y - a.y, dz = b.z - a.z
        const distSq = dx * dx + dy * dy + dz * dz || 1
        const dist = Math.sqrt(distSq)
        const f = CHARGE_STRENGTH * alpha / distSq
        const fx = f * dx / dist, fy = f * dy / dist, fz = f * dz / dist
        a.vx += fx; a.vy += fy; a.vz += fz
        b.vx -= fx; b.vy -= fy; b.vz -= fz
      }
    }

    for (const { source, target } of simLinks) {
      const dx = target.x - source.x, dy = target.y - source.y, dz = target.z - source.z
      const dist = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1
      const f = (dist - LINK_DISTANCE) * LINK_STRENGTH * alpha
      const fx = f * dx / dist, fy = f * dy / dist, fz = f * dz / dist
      source.vx += fx; source.vy += fy; source.vz += fz
      target.vx -= fx; target.vy -= fy; target.vz -= fz
    }

    for (const node of simNodes) {
      node.vx -= node.x * CENTER_STRENGTH * alpha
      node.vy -= node.y * CENTER_STRENGTH * alpha
      node.vz -= node.z * CENTER_STRENGTH * alpha
    }

    for (const node of simNodes) {
      node.vx *= 1 - VELOCITY_DECAY
      node.vy *= 1 - VELOCITY_DECAY
      node.vz *= 1 - VELOCITY_DECAY
      node.x += node.vx
      node.y += node.vy
      node.z += node.vz
      node.mesh.position.set(node.x, node.y, node.z)
    }

    if (edgePositions) {
      for (let i = 0; i < simLinks.length; i++) {
        const { source, target } = simLinks[i]
        const j = i * 6
        edgePositions[j] = source.x
        edgePositions[j + 1] = source.y
        edgePositions[j + 2] = source.z
        edgePositions[j + 3] = target.x
        edgePositions[j + 4] = target.y
        edgePositions[j + 5] = target.z
      }
      if (edgeLine) edgeLine.geometry.attributes.position.needsUpdate = true
    }

    alpha *= 1 - ALPHA_DECAY
  }

  function animate() {
    animFrameId = requestAnimationFrame(animate)
    simulationTick()
    controls?.update()
    renderer?.render(scene, camera)
  }

  function handlePointerMove(event) {
    if (!renderer || !camera || !nodeGroup) return
    const rect = renderer.domElement.getBoundingClientRect()
    pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1
    pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1

    raycaster.setFromCamera(pointer, camera)
    const intersects = raycaster.intersectObjects(nodeGroup.children, false)

    if (prevHoveredMesh) {
      prevHoveredMesh.material.emissiveIntensity = 0.3
      prevHoveredMesh.scale.setScalar(1)
      prevHoveredMesh = null
    }

    if (intersects.length > 0) {
      const mesh = intersects[0].object
      mesh.material.emissiveIntensity = 0.7
      mesh.scale.setScalar(1.3)
      prevHoveredMesh = mesh
      renderer.domElement.style.cursor = 'pointer'

      const worldPos = mesh.position.clone()
      const screenPos = worldPos.project(camera)
      const sx = (screenPos.x * 0.5 + 0.5) * rect.width
      const sy = (-screenPos.y * 0.5 + 0.5) * rect.height

      onNodeHover?.(mesh.userData.nodeId, mesh.userData.nodeData, { x: sx, y: sy })
    } else {
      renderer.domElement.style.cursor = 'default'
      onNodeHover?.(null, null, null)
    }
  }

  function handleClick(event) {
    if (!renderer || !camera || !nodeGroup) return
    const rect = renderer.domElement.getBoundingClientRect()
    const px = ((event.clientX - rect.left) / rect.width) * 2 - 1
    const py = -((event.clientY - rect.top) / rect.height) * 2 + 1

    raycaster.setFromCamera(new THREE.Vector2(px, py), camera)
    const intersects = raycaster.intersectObjects(nodeGroup.children, false)

    if (intersects.length > 0) {
      onNodeClick?.(intersects[0].object.userData.nodeId, intersects[0].object.userData.nodeData)
    } else {
      onNodeClick?.(null, null)
    }
  }

  function handleResize() {
    if (!container || !renderer || !camera) return
    const w = container.clientWidth
    const h = container.clientHeight
    if (!w || !h) return
    camera.aspect = w / h
    camera.updateProjectionMatrix()
    renderer.setSize(w, h)
  }

  function setDarkMode(isDark) {
    if (!scene) return
    const bg = isDark ? 0x0a0a1a : 0xf8f9fa
    scene.background.set(bg)
    if (scene.fog) scene.fog.color.set(bg)
    if (edgeLine) {
      edgeLine.material.color.set(isDark ? 0x4488ff : 0x2068ff)
      edgeLine.material.opacity = isDark ? 0.18 : 0.14
    }
  }

  function dispose() {
    if (animFrameId) cancelAnimationFrame(animFrameId)
    animFrameId = null
    renderer?.domElement?.removeEventListener('pointermove', handlePointerMove)
    renderer?.domElement?.removeEventListener('click', handleClick)
    if (resizeObserver) { resizeObserver.disconnect(); resizeObserver = null }
    controls?.dispose()
    clearObjects()
    renderer?.dispose()
    if (container && renderer?.domElement?.parentNode === container) {
      container.removeChild(renderer.domElement)
    }
    container = null
    renderer = null
    scene = null
    camera = null
    controls = null
  }

  return {
    init,
    setData,
    setDarkMode,
    reheat() { alpha = 1.0 },
    dispose,
  }
}
