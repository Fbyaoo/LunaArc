<template>
  <canvas
    ref="canvas"
    class="curtain-canvas"
    @mousemove="handleMouseMove"
    @mouseleave="handleMouseLeave"
  />
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from "vue"
import logoMaskSrc from "@/assets/landing/lunaarc-mask.png"

interface Bead {
  baseX: number
  baseY: number
  x: number
  y: number
  isLogo: boolean
  alpha: number
  amp: number
}

interface ColumnState {
  x: number
  length: number
  phase: number
  sway: number
  velocity: number
  target: number
  impulse: number
  beads: Bead[]
}

const canvas = ref<HTMLCanvasElement | null>(null)
let ctx: CanvasRenderingContext2D | null = null
let width = 0
let height = 0
let dpr = 1
let raf = 0
let resizeTimeout: any = null
let whiteSprite: HTMLCanvasElement | null = null
let blueSprite: HTMLCanvasElement | null = null

const config = {
  columnSpacing: 10,
  minBeads: 65,
  maxBeads: 110,
  beadGap: 12,
  beadRadius: 2.5,
  baseAlpha: 0.22,
  logoAlphaBoost: 0.35,
  waveSpeed: 0.00075,
  baseAmplitude: 45,
  mouseRadius: 260,
  mouseImpulse: 1.5,
  neighborCoupling: 0.035,
  springStrength: 0.018,
  damping: 0.94,
  logoTopRatio: 0.30,
  logoWidthRatio: 0.58,
  logoHeightRatio: 0.18,
  bottomFadeStart: 0.88
}

let columns: ColumnState[] = []
let logoMask: boolean[][] = []
let shortestHeight = 0

function random(min: number, max: number) {
  return Math.random() * (max - min) + min
}

function loadImage(src: string) {
  return new Promise<HTMLImageElement>((resolve) => {
    const img = new Image()
    img.onload = () => resolve(img)
    img.src = src
  })
}

function createSprite(radius: number, color: string, shadowColor: string, blur: number) {
  const size = (radius + blur) * 2 + 4
  const c = document.createElement("canvas")
  c.width = size
  c.height = size
  const context = c.getContext("2d")!
  context.shadowColor = shadowColor
  context.shadowBlur = blur
  context.beginPath()
  context.arc(size / 2, size / 2, radius, 0, Math.PI * 2)
  context.fillStyle = color
  context.fill()
  return c
}

async function buildLogo() {
  const img = await loadImage(logoMaskSrc)
  const cols = Math.floor(columns.length * config.logoWidthRatio)
  const rows = Math.floor(100 * config.logoHeightRatio)

  const temp = document.createElement("canvas")
  temp.width = cols
  temp.height = rows
  const c = temp.getContext("2d")
  if (!c) return

  c.drawImage(img, 0, 0, cols, rows)
  const data = c.getImageData(0, 0, cols, rows).data

  logoMask = []
  for (let y = 0; y < rows; y++) {
    const row: boolean[] = []
    for (let x = 0; x < cols; x++) {
      const id = (y * cols + x) * 4
      row.push(data[id + 3] > 40)
    }
    logoMask.push(row)
  }
}

function createScene() {
  columns = []
  const count = Math.ceil(width / config.columnSpacing)
  let min = 99999

  for (let i = 0; i < count; i++) {
    const length = Math.floor(random(config.minBeads, config.maxBeads))
    const beads: Bead[] = []

    for (let j = 0; j < length; j++) {
      const depth = length <= 1 ? 0 : j / (length - 1)
      beads.push({
        baseX: i * config.columnSpacing,
        baseY: j * config.beadGap,
        x: i * config.columnSpacing,
        y: j * config.beadGap,
        isLogo: false,
        alpha: config.baseAlpha,
        amp: Math.pow(depth, 1.25)
      })
    }

    min = Math.min(min, length * config.beadGap)

    columns.push({
      x: i * config.columnSpacing,
      length,
      phase: i * 0.15,
      sway: 0,
      velocity: 0,
      target: 0,
      impulse: 0,
      beads
    })
  }

  shortestHeight = min
}

function applyLogo() {
  if (!logoMask.length) return
  const rows = logoMask.length
  const cols = logoMask[0].length
  const startX = Math.floor((columns.length - cols) / 2)
  const startY = Math.floor((columns[0]?.length || 0) * config.logoTopRatio)

  for (let x = 0; x < cols; x++) {
    for (let y = 0; y < rows; y++) {
      if (!logoMask[y][x]) continue
      const column = columns[startX + x]
      if (!column) continue
      const bead = column.beads[startY + y]
      if (bead) bead.isLogo = true
    }
  }
}

async function resize() {
  if (!canvas.value) return
  width = window.innerWidth
  height = window.innerHeight
  dpr = window.devicePixelRatio || 1

  canvas.value.width = width * dpr
  canvas.value.height = height * dpr
  canvas.value.style.width = width + "px"
  canvas.value.style.height = height + "px"

  ctx = canvas.value.getContext("2d")
  if (ctx) ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

  whiteSprite = createSprite(config.beadRadius, 'rgba(255,255,255,1)', 'rgba(255,255,255,.4)', 3)
  blueSprite = createSprite(config.beadRadius, 'rgba(0,51,160,1)', 'rgba(0,51,160,.8)', 8)

  createScene()
  await buildLogo()
  applyLogo()
}

function physics(time: number) {
  const old = columns.map(c => c.sway)

  for (let i = 0; i < columns.length; i++) {
    const c = columns[i]
    const left = old[i - 1] ?? old[i]
    const right = old[i + 1] ?? old[i]
    const neighbor = (left + right) / 2
    const wave = Math.sin(time * config.waveSpeed + i * 0.08)
    const wind = wave * config.baseAmplitude

    c.target = wind + neighbor * config.neighborCoupling
    c.velocity += (c.target - c.sway) * config.springStrength
    c.velocity += c.impulse
    c.impulse *= 0.86
    c.velocity *= config.damping
    c.sway += c.velocity
  }
}

function updateBeads(time: number) {
  for (const c of columns) {
    for (let i = 0; i < c.beads.length; i++) {
      const bead = c.beads[i]
      const depth = i / c.beads.length
      const tail = depth > 0.8 ? Math.sin(time * 0.002 + i) * 5 : 0

      bead.x = bead.baseX + c.sway * bead.amp + tail

      const fade = Math.max(0, 1 - Math.max(0, bead.baseY - height * config.bottomFadeStart) / (height * (1 - config.bottomFadeStart)))
      bead.alpha = config.baseAlpha * fade
    }
  }
}

function draw() {
  if (!ctx || !whiteSprite || !blueSprite) return
  ctx.clearRect(0, 0, width, height)

  const halfSize = whiteSprite.width / 2

  for (const c of columns) {
    for (const b of c.beads) {
      ctx.globalAlpha = b.isLogo ? Math.min(b.alpha + config.logoAlphaBoost, 1) : b.alpha
      if (b.isLogo) {
        ctx.drawImage(blueSprite, b.x - halfSize, b.y - halfSize)
      } else {
        ctx.drawImage(whiteSprite, b.x - halfSize, b.y - halfSize)
      }
    }
  }
  ctx.globalAlpha = 1
}

function animate(t: number) {
  physics(t)
  updateBeads(t)
  draw()
  raf = requestAnimationFrame(animate)
}

function handleResize() {
  clearTimeout(resizeTimeout)
  resizeTimeout = setTimeout(() => {
    resize()
  }, 200)
}

function handleMouseMove(e: MouseEvent) {
  const x = e.clientX
  const dx = e.movementX

  for (let i = 0; i < columns.length; i++) {
    const c = columns[i]
    const dis = Math.abs(c.x - x)
    if (dis < config.mouseRadius) {
      const force = 1 - dis / config.mouseRadius
      c.impulse += dx * force * 0.012
    }
  }
}

function handleMouseLeave() {}

onMounted(async () => {
  await resize()
  window.addEventListener("resize", handleResize)
  raf = requestAnimationFrame(animate)
})

onBeforeUnmount(() => {
  cancelAnimationFrame(raf)
  window.removeEventListener("resize", handleResize)
  clearTimeout(resizeTimeout)
})
</script>

<style scoped>
.curtain-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 20;
}
</style>