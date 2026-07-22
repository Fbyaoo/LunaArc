import type { GestureEvent, YoloGesturePayload } from '@/types/gesture'

export interface YoloGestureClientOptions {
  url: string
  onGesture: (event: GestureEvent) => void
  onStatus?: (status: 'connecting' | 'open' | 'closed' | 'error') => void
}

export class YoloGestureClient {
  private socket: WebSocket | null = null
  private readonly options: YoloGestureClientOptions

  constructor(options: YoloGestureClientOptions) {
    this.options = options
  }

  connect(): void {
    if (!this.options.url || this.socket) return
    this.options.onStatus?.('connecting')
    this.socket = new WebSocket(this.options.url)

    this.socket.addEventListener('open', () => this.options.onStatus?.('open'))
    this.socket.addEventListener('close', () => {
      this.options.onStatus?.('closed')
      this.socket = null
    })
    this.socket.addEventListener('error', () => this.options.onStatus?.('error'))
    this.socket.addEventListener('message', (message) => {
      try {
        const payload = JSON.parse(String(message.data)) as YoloGesturePayload
        this.options.onGesture({
          source: 'yolo',
          gesture: payload.gesture,
          confidence: payload.confidence,
          action: payload.action,
          timestamp: payload.timestamp ?? Date.now(),
        })
      } catch {
        // Ignore malformed backend events instead of interrupting the reading.
      }
    })
  }

  sendFrame(blob: Blob): void {
    if (this.socket?.readyState === WebSocket.OPEN) this.socket.send(blob)
  }

  disconnect(): void {
    this.socket?.close()
    this.socket = null
  }
}
