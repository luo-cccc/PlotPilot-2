import { apiClient, resolveHttpUrl } from './config'

export interface AutopilotStatus {
  autopilot_status: 'stopped' | 'running' | 'error' | 'completed'
  current_stage: string
  current_act: number
  current_chapter_in_act: number
  current_beat_index: number
  current_auto_chapters: number
  max_auto_chapters: number
  progress_pct: number
  manuscript_chapters: number
  progress_pct_manuscript: number
  current_chapter_number: number | null
  needs_review: boolean
  last_chapter_audit?: {
    passed: boolean
    quality_scores: Record<string, number>
    issues: string[]
  }
}

export interface CircuitBreakerStatus {
  status: 'open' | 'closed' | 'half_open'
  error_count: number
  max_errors: number
  last_error?: {
    message: string
    timestamp: string
    context?: string
  }
  error_history?: {
    message: string
    timestamp: string
    context?: string
  }[]
}

export const autopilotApi = {
  /** GET /autopilot/{novelId}/status */
  getStatus: (novelId: string): Promise<AutopilotStatus> =>
    apiClient.get<AutopilotStatus>(`/autopilot/${novelId}/status`),

  /** POST /autopilot/{novelId}/start */
  start: (novelId: string, body?: Record<string, unknown>): Promise<void> =>
    apiClient.post<void>(`/autopilot/${novelId}/start`, body ?? {}),

  /** POST /autopilot/{novelId}/stop */
  stop: (novelId: string): Promise<void> =>
    apiClient.post<void>(`/autopilot/${novelId}/stop`),

  /** POST /autopilot/{novelId}/resume */
  resume: (novelId: string): Promise<void> =>
    apiClient.post<void>(`/autopilot/${novelId}/resume`),

  /** GET /autopilot/{novelId}/circuit-breaker */
  getCircuitBreaker: (novelId: string): Promise<CircuitBreakerStatus> =>
    apiClient.get<CircuitBreakerStatus>(`/autopilot/${novelId}/circuit-breaker`),

  /** POST /autopilot/{novelId}/circuit-breaker/reset */
  resetCircuitBreaker: (novelId: string): Promise<void> =>
    apiClient.post<void>(`/autopilot/${novelId}/circuit-breaker/reset`),

  /** SSE /autopilot/{novelId}/stream */
  streamUrl: (novelId: string, afterSeq?: number): string => {
    const q = afterSeq && afterSeq > 0 ? `?after_seq=${afterSeq}` : ''
    return resolveHttpUrl(`/autopilot/${novelId}/stream${q}`)
  },

  /** GET /autopilot/{novelId}/events */
  getEvents: (novelId: string): Promise<unknown[]> =>
    apiClient.get<unknown[]>(`/autopilot/${novelId}/events`),
}
