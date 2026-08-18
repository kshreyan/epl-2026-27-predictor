#!/usr/bin/env node
// Copies the pipeline's real dashboard JSON (data/outputs/dashboard/*.json)
// into site/public/data/ so both `vite dev` and `vite build` always read
// current, real data -- never a hand-maintained or stale copy. Runs as
// `predev` and `prebuild` (see package.json).
import { existsSync, mkdirSync, readdirSync, copyFileSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const SOURCE_DIR = join(__dirname, '..', '..', 'data', 'outputs', 'dashboard')
const DEST_DIR = join(__dirname, '..', 'public', 'data')

if (!existsSync(SOURCE_DIR)) {
  console.error(
    `No dashboard data found at ${SOURCE_DIR}.\n` +
    `Run the Python pipeline first: python -m src.dashboard.build_dashboard_json`
  )
  process.exit(1)
}

mkdirSync(DEST_DIR, { recursive: true })
const files = readdirSync(SOURCE_DIR).filter((f) => f.endsWith('.json'))
for (const file of files) {
  copyFileSync(join(SOURCE_DIR, file), join(DEST_DIR, file))
}
console.log(`Synced ${files.length} dashboard JSON file(s) from ${SOURCE_DIR} -> ${DEST_DIR}`)
