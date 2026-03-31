/**
 * Post-build optimization checks for the frontend bundle.
 * Warns (never fails the build) when optimizations regress.
 *
 * Checks:
 *  1. Bundle size targets (main < 200KB gzip, largest lazy chunk < 100KB gzip)
 *  2. No console.log / console.debug in source
 *  3. All view routes are lazy-loaded (except LandingView)
 *  4. No wildcard d3 imports (`import * as d3`)
 *  5. No unused package.json dependencies
 */

import { readFileSync, readdirSync, statSync, existsSync } from 'node:fs'
import { join, resolve, extname } from 'node:path'
import { gzipSync } from 'node:zlib'
import { createRequire } from 'node:module'

const ROOT = resolve(import.meta.dirname, '..')
const DIST = join(ROOT, 'dist')
const SRC = join(ROOT, 'src')

const WARN = '\x1b[33m⚠\x1b[0m'
const PASS = '\x1b[32m✓\x1b[0m'
const HEADER = '\x1b[36m'
const RESET = '\x1b[0m'

let warnings = 0

function warn(msg) {
  console.log(`  ${WARN}  ${msg}`)
  warnings++
}

function pass(msg) {
  console.log(`  ${PASS}  ${msg}`)
}

function heading(title) {
  console.log(`\n${HEADER}── ${title} ──${RESET}`)
}

function formatKB(bytes) {
  return (bytes / 1024).toFixed(1) + ' KB'
}

function gzipSize(filePath) {
  const buf = readFileSync(filePath)
  return gzipSync(buf).length
}

function collectFiles(dir, extensions) {
  const results = []
  if (!existsSync(dir)) return results
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name)
    if (entry.isDirectory()) {
      results.push(...collectFiles(full, extensions))
    } else if (extensions.includes(extname(entry.name))) {
      results.push(full)
    }
  }
  return results
}

// ─── 1. Bundle size ──────────────────────────────────────────────────

function checkBundleSize() {
  heading('Bundle Size')

  const MAIN_LIMIT = 200 * 1024
  const CHUNK_LIMIT = 100 * 1024

  if (!existsSync(DIST)) {
    warn('dist/ directory not found — skipping size checks')
    return
  }

  const assetsDir = join(DIST, 'assets')
  if (!existsSync(assetsDir)) {
    warn('dist/assets/ not found — skipping size checks')
    return
  }

  const jsFiles = readdirSync(assetsDir)
    .filter(f => f.endsWith('.js'))
    .map(f => {
      const full = join(assetsDir, f)
      const raw = statSync(full).size
      const gz = gzipSize(full)
      return { name: f, raw, gz }
    })

  const mainEntry = jsFiles.find(f => /^index[-.]/.test(f.name))
  const chunks = jsFiles.filter(f => f !== mainEntry)

  if (mainEntry) {
    if (mainEntry.gz > MAIN_LIMIT) {
      warn(`Main bundle ${mainEntry.name}: ${formatKB(mainEntry.gz)} gzip (limit: ${formatKB(MAIN_LIMIT)})`)
    } else {
      pass(`Main bundle ${mainEntry.name}: ${formatKB(mainEntry.gz)} gzip (limit: ${formatKB(MAIN_LIMIT)})`)
    }
  }

  const largestChunk = chunks.sort((a, b) => b.gz - a.gz)[0]
  if (largestChunk) {
    if (largestChunk.gz > CHUNK_LIMIT) {
      warn(`Largest chunk ${largestChunk.name}: ${formatKB(largestChunk.gz)} gzip (limit: ${formatKB(CHUNK_LIMIT)})`)
    } else {
      pass(`Largest chunk ${largestChunk.name}: ${formatKB(largestChunk.gz)} gzip (limit: ${formatKB(CHUNK_LIMIT)})`)
    }
  }

  const totalGz = jsFiles.reduce((s, f) => s + f.gz, 0)
  console.log(`     Total JS: ${formatKB(totalGz)} gzip across ${jsFiles.length} files`)
}

// ─── 2. No console.log / console.debug in source ────────────────────

function checkConsoleLogs() {
  heading('Console Statements')

  const sourceFiles = collectFiles(SRC, ['.js', '.ts', '.vue'])
  const hits = []

  for (const file of sourceFiles) {
    const content = readFileSync(file, 'utf8')
    const lines = content.split('\n')
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]
      if (/console\.(log|debug)\s*\(/.test(line) && !/\/\/.*console/.test(line)) {
        hits.push({ file: file.replace(ROOT + '/', ''), line: i + 1 })
      }
    }
  }

  if (hits.length > 0) {
    warn(`Found ${hits.length} console.log/debug statement(s):`)
    for (const h of hits.slice(0, 10)) {
      console.log(`         ${h.file}:${h.line}`)
    }
    if (hits.length > 10) console.log(`         ... and ${hits.length - 10} more`)
  } else {
    pass('No console.log/debug found in source')
  }
}

// ─── 3. Lazy route configuration ────────────────────────────────────

function checkLazyRoutes() {
  heading('Lazy Routes')

  const routerFile = join(SRC, 'router', 'index.js')
  if (!existsSync(routerFile)) {
    warn('router/index.js not found — skipping lazy route check')
    return
  }

  const content = readFileSync(routerFile, 'utf8')

  const staticImports = [...content.matchAll(/^import\s+\w+\s+from\s+['"]\.\.\/views\/(\w+)\.vue['"]/gm)]
  const lazyImports = [...content.matchAll(/\(\)\s*=>\s*import\(['"]\.\.\/views\/(\w+)\.vue['"]\)/g)]

  const allowedStatic = ['LandingView']
  const badStatic = staticImports
    .map(m => m[1])
    .filter(name => !allowedStatic.includes(name))

  if (badStatic.length > 0) {
    warn(`Non-lazy view imports (should use dynamic import): ${badStatic.join(', ')}`)
  } else {
    pass(`All views lazy-loaded (${lazyImports.length} lazy, ${staticImports.length} static allowed: ${allowedStatic.join(', ')})`)
  }
}

// ─── 4. No wildcard d3 imports ──────────────────────────────────────

function checkD3Imports() {
  heading('D3 Imports')

  const sourceFiles = collectFiles(SRC, ['.js', '.ts', '.vue'])
  const hits = []

  for (const file of sourceFiles) {
    const content = readFileSync(file, 'utf8')
    const lines = content.split('\n')
    for (let i = 0; i < lines.length; i++) {
      if (/import\s+\*\s+as\s+d3\s+from\s+['"]d3['"]/.test(lines[i])) {
        hits.push({ file: file.replace(ROOT + '/', ''), line: i + 1 })
      }
    }
  }

  if (hits.length > 0) {
    warn(`Found ${hits.length} wildcard d3 import(s) — use named imports from 'd3' instead:`)
    for (const h of hits) {
      console.log(`         ${h.file}:${h.line}`)
    }
  } else {
    pass('No wildcard d3 imports found')
  }
}

// ─── 5. Unused dependencies ─────────────────────────────────────────

function checkUnusedDeps() {
  heading('Unused Dependencies')

  const pkgPath = join(ROOT, 'package.json')
  if (!existsSync(pkgPath)) {
    warn('package.json not found — skipping dependency check')
    return
  }

  const pkg = JSON.parse(readFileSync(pkgPath, 'utf8'))
  const deps = Object.keys(pkg.dependencies || {})

  const sourceFiles = collectFiles(SRC, ['.js', '.ts', '.vue'])
  const allSource = sourceFiles.map(f => readFileSync(f, 'utf8')).join('\n')

  const configFiles = ['vite.config.js', 'vite.config.ts', 'tailwind.config.js', 'tailwind.config.ts', 'postcss.config.js']
    .map(f => join(ROOT, f))
    .filter(f => existsSync(f))
    .map(f => readFileSync(f, 'utf8'))
    .join('\n')

  const allContent = allSource + '\n' + configFiles

  const unused = deps.filter(dep => {
    const patterns = [
      `from ['"]${dep}['"]`,
      `from ['"]${dep}/`,
      `import\\(['"]${dep}['"]\\)`,
      `import\\(['"]${dep}/`,
      `require\\(['"]${dep}['"]\\)`,
      `require\\(['"]${dep}/`,
    ]
    return !patterns.some(p => new RegExp(p).test(allContent))
  })

  if (unused.length > 0) {
    warn(`Potentially unused dependencies: ${unused.join(', ')}`)
  } else {
    pass(`All ${deps.length} dependencies appear used`)
  }
}

// ─── Run all checks ─────────────────────────────────────────────────

console.log(`\n${'═'.repeat(50)}`)
console.log('  Build Optimization Report')
console.log('═'.repeat(50))

checkBundleSize()
checkConsoleLogs()
checkLazyRoutes()
checkD3Imports()
checkUnusedDeps()

console.log(`\n${'─'.repeat(50)}`)
if (warnings > 0) {
  console.log(`  ${WARN}  ${warnings} warning(s) — consider fixing before deploy`)
} else {
  console.log(`  ${PASS}  All checks passed!`)
}
console.log('─'.repeat(50) + '\n')
