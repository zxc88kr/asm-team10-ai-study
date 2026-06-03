export type Status = 'full' | 'partial' | 'none'
export type NightTransit = 'good' | 'ok' | 'poor'
export type CardSource = 'said' | 'inferred'
export type ActiveView = 'chat' | 'analysis'

export interface NightInfo {
  lit: boolean
  mainRoad: boolean
  alleyM: number
}

export interface CommuteLeg {
  label: string
  minutes: number
  type: 'walk' | 'subway' | 'bus'
}

export interface CommuteAnalysis {
  legs: CommuteLeg[]
  totalMinutes: number
  transfers: number
  mainNote: string
}

export interface NightSafetyItem {
  icon: string
  label: string
  detail: string
  pass: boolean
}

export interface ConvenienceFacility {
  name: string
  walkMin: number
  icon: string
}

export interface RecommendationBasis {
  category: string
  color: string
  icon: string
  detail: string
}

export interface LocationAnalysis {
  commute: CommuteAnalysis
  nightSafety: NightSafetyItem[]
  convenience: ConvenienceFacility[]
  basis: RecommendationBasis[]
  pros: string[]
  cons: string[]
  aiComment: string
  scoreBreakdown: { label: string; score: number }[]
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
  commuteMin: number
  night: NightInfo
  nightTransit: NightTransit
  thumb: string
  desc: string
  locationAnalysis: LocationAnalysis
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
  commuteMax?: number
  noBasement?: boolean
}

export interface Message {
  role: 'ai' | 'user'
  text: string
  searching?: boolean
}

export interface ScenarioStep {
  userText: string
  hard?: HardConstraints
  cards?: string[]
  aiText: string
  recommend?: boolean
}
