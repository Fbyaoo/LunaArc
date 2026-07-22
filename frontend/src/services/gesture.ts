export type GestureSource = 'mediapipe' | 'yolo' | 'pointer' | 'keyboard'
export type GestureAction =
  | 'rotate'
  | 'shuffle'
  | 'select'
  | 'confirm'
  | 'reset'
  | 'stop'
  | 'switch_spread'
  | 'request_reading'

export interface GestureEvent {
  source: GestureSource
  gesture: string
  action: GestureAction
  confidence: number
  delta?: number
  timestamp: number
}

export interface YoloGesturePayload {
  gesture: string
  confidence: number
  action: GestureAction
  timestamp?: number
}
