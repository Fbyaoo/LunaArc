import { FilesetResolver, HandLandmarker, type NormalizedLandmark } from '@mediapipe/tasks-vision'
import type { GestureEvent } from '@/types/gesture'

export interface MediaPipeGestureOptions {
  video: HTMLVideoElement
  onGesture: (event: GestureEvent) => void
  onFrame?: (video: HTMLVideoElement) => void
}

export class MediaPipeGestureController {
  private readonly options: MediaPipeGestureOptions
  private landmarker: HandLandmarker | null = null
  private stream: MediaStream | null = null
  private frameId = 0
  private lastVideoTime = -1
  private lastPalmX: number | null = null
  private smoothPalmX: number | null = null
  private pinchStartedAt: number | null = null
  private fistStartedAt: number | null = null
  private lastDiscreteActionAt = 0
  private active = false

  constructor(options: MediaPipeGestureOptions) {
    this.options = options
  }

  async start(): Promise<void> {
    const vision = await FilesetResolver.forVisionTasks(
      'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm',
    )

    this.landmarker = await HandLandmarker.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath:
          'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task',
        delegate: 'GPU',
      },
      runningMode: 'VIDEO',
      numHands: 2,
      minHandDetectionConfidence: 0.65,
      minHandPresenceConfidence: 0.65,
      minTrackingConfidence: 0.65,
    })

    this.stream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'user', width: 960, height: 720 },
      audio: false,
    })
    this.options.video.srcObject = this.stream
    await this.options.video.play()
    this.active = true
    this.render()
  }

  private render = (): void => {
    if (!this.active || !this.landmarker) return
    const video = this.options.video
    if (video.currentTime !== this.lastVideoTime && video.readyState >= 2) {
      const now = performance.now()
      const result = this.landmarker.detectForVideo(video, now)
      this.lastVideoTime = video.currentTime
      this.process(result.landmarks)
      this.options.onFrame?.(video)
    }
    this.frameId = requestAnimationFrame(this.render)
  }

  private process(hands: NormalizedLandmark[][]): void {
    if (hands.length === 0) {
      this.lastPalmX = null
      this.smoothPalmX = null
      this.pinchStartedAt = null
      this.fistStartedAt = null
      return
    }

    if (hands.length >= 2) {
      const a = hands[0][9]
      const b = hands[1][9]
      const distance = Math.hypot(a.x - b.x, a.y - b.y)
      if (distance < 0.12) this.emit('two_hands_close', 'stop', 0.9)
      if (distance > 0.42) this.emit('two_hands_open', 'reset', 0.9)
      return
    }

    const hand = hands[0]
    const rawX = hand[9].x
    this.smoothPalmX = this.smoothPalmX === null ? rawX : this.smoothPalmX * 0.78 + rawX * 0.22
    if (this.lastPalmX !== null) {
      const delta = this.smoothPalmX - this.lastPalmX
      if (Math.abs(delta) > 0.0025) {
        this.options.onGesture({
          source: 'mediapipe',
          gesture: 'palm_move',
          action: 'rotate',
          confidence: 1,
          delta: delta * 720,
          timestamp: Date.now(),
        })
      }
    }
    this.lastPalmX = this.smoothPalmX

    const palmY = hand[9].y
    const isFist = [8, 12, 16, 20].every((index) => hand[index].y > palmY)
    this.fistStartedAt = isFist ? (this.fistStartedAt ?? Date.now()) : null
    if (this.fistStartedAt && Date.now() - this.fistStartedAt > 420) {
      this.emit('fist', 'shuffle', 0.88)
      this.fistStartedAt = null
    }

    const pinchDistance = Math.hypot(hand[4].x - hand[8].x, hand[4].y - hand[8].y)
    this.pinchStartedAt = pinchDistance < 0.055 ? (this.pinchStartedAt ?? Date.now()) : null
    if (this.pinchStartedAt && Date.now() - this.pinchStartedAt > 520) {
      this.emit('pinch', 'select', 0.92)
      this.pinchStartedAt = null
    }
  }

  private emit(gesture: string, action: GestureEvent['action'], confidence: number): void {
    const now = Date.now()
    if (now - this.lastDiscreteActionAt < 900) return
    this.lastDiscreteActionAt = now
    this.options.onGesture({ source: 'mediapipe', gesture, action, confidence, timestamp: now })
  }

  stop(): void {
    this.active = false
    cancelAnimationFrame(this.frameId)
    this.stream?.getTracks().forEach((track) => track.stop())
    this.options.video.srcObject = null
    this.landmarker?.close()
    this.landmarker = null
    this.stream = null
  }
}
