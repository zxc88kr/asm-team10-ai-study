export type Status = 'full' | 'partial' | 'none'
export type NightTransit = 'good' | 'ok' | 'poor'
export type CardSource = 'said' | 'inferred'

export interface NightInfo {
  lit: boolean
  mainRoad: boolean
  alleyM: number
}

export interface Listing {
  id: string
  name: string
  type: string
  area: string
  deposit: number
  rent: number
  pyeong: number
  floor: number
  options: string[]
  walkMin: number
  night: NightInfo
  nightTransit: NightTransit
  thumb: string
  desc: string
}

export interface MatchResult {
  status: Status
  evidence: string
}

export interface ConditionCard {
  label: string
  category: string
  weight: number
  source: CardSource
  reason: string
  match(L: Listing): MatchResult
}

export interface BreakdownItem extends MatchResult {
  cid: string
  label: string
  category: string
  weight: number
}

export interface ScoredListing {
  L: Listing
  excluded: boolean
  score: number
  breakdown: BreakdownItem[]
  penalty: number
  reason?: string
}

export interface HardConstraints {
  deposit?: number
  rent?: number
}

export interface Message {
  role: 'ai' | 'user'
  text: string
}

export interface ScenarioStep {
  userText: string
  hard?: HardConstraints
  cards?: string[]
  aiText: string
  recommend?: boolean
}
