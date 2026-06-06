// 백엔드(LangGraph) SSE 이벤트/엔티티 타입. backend/app/state.py 의 camelCase 직렬화와 1:1.

export type LiveSource = 'said' | 'extracted' | 'discovered'
export type LiveStatus = 'full' | 'partial' | 'none'

export interface LiveCard {
  id: string
  label: string
  category: string
  kind: 'hard' | 'soft'
  weight: number
  source: LiveSource
  reason: string
  confidence: number
}

export interface LiveMatch {
  cardId: string
  status: LiveStatus
  evidence: string
  grounded: boolean | null
}

export interface LiveRanked {
  listingId: string
  score: number
  excluded: boolean
  breakdown: LiveMatch[]
  penalty: number
  tradeoff: string | null
}

export interface LiveListing {
  id: string
  name: string
  type: string
  area: string
  deposit: number
  rent: number
  mgmtFee: number
  pyeong: number
  floor: number
  options: string[]
  desc: string
  geo: Record<string, unknown>
  location: Record<string, unknown>
}

export interface LiveMetric {
  ratio: string
  said: number
  derived: number
}

export interface LiveQuestion {
  questionType: string
  category?: string
  text?: string
  categories?: string[]
  options?: string[]
}

// SSE 로 흐르는 이벤트(공통 type 필드로 구분)
export type LiveEvent =
  | ({ type: 'card'; card: LiveCard })
  | ({ type: 'metric' } & LiveMetric)
  | ({ type: 'question' } & LiveQuestion)
  | ({ type: 'ranked'; ranked: LiveRanked[]; grounded?: boolean })
  | ({ type: 'location'; listingId: string; analysis: Record<string, unknown> })
  | ({ type: 'message'; role: 'ai' | 'user'; text: string })
  | ({ type: 'done' })
