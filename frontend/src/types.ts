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

export interface AgentPropertyItem {
  property_id: string
  title: string
  type: string
  score: number
  deposit: number
  monthly_rent: number
  location: string
  address_detail: string
  description: string
  facilities: string[]
  transit_walk_min: number
  transit_station: string
  soft_card_matches: { card: string; matched: boolean | 'partial'; evidence: string }[]
  agent_mode: string
}

export interface AgentRecommendResponse {
  session_id: string
  top_properties: AgentPropertyItem[]
}

export interface AgentConditions {
  session_id: string
  hard_conditions: {
    location_transport: {
      areas: string[]
      landmarks: string[]
      commute_time_max_minutes: number | null
      transport_notes: string[]
    }
    monthly_rent: {
      max_krw: number | null
      max_manwon: number | null
      includes_management_fee: boolean | null
    }
  }
  soft_conditions: {
    convenience_facilities: {
      required: string[]
      preferred: string[]
      notes: string[]
    }
    pests: {
      avoid: boolean | null
      evidence: string[]
    }
    default_options: {
      required: string[]
      preferred: string[]
    }
    basement: {
      avoid: boolean | null
      evidence: string[]
    }
    mold: {
      avoid: boolean | null
      evidence: string[]
    }
    extra_notes: string[]
  }
  missing_required_conditions: string[]
  next_question: string
  is_complete?: boolean
  next_action?: 'ask_required_conditions' | 'ask_soft_conditions' | 'recommend_listings'
}
