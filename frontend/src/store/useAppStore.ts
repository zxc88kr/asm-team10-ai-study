import { create } from 'zustand'
import { GREETING } from '../data/scenario'
import { CONDITION_CARDS } from '../data/conditions'
import { LISTINGS } from '../data/listings'
import { postMessage, postRecommend } from '../services/agentApi'
import type {
  Listing,
  HardConstraints,
  Message,
  ScoredListing,
  Status,
  BreakdownItem,
  ActiveView,
  AgentConditions,
  AgentPropertyItem,
  LocationAnalysis,
  NightSafetyItem,
  ConvenienceFacility,
  RecommendationBasis,
} from '../types'

const RENT_ALLOWANCE = 5
const STATUS_VAL: Record<Status, number> = { full: 1, partial: 0.5, none: 0 }

export const STATUS_KO: Record<Status, string> = { full: '충족', partial: '부분', none: '미흡' }

export function scoreClass(score: number): string {
  if (score >= 85) return 'sc-high'
  if (score >= 75) return 'sc-mid'
  return 'sc-low'
}

type ScoreResult =
  | { excluded: true; reason: string }
  | { excluded: false; score: number; breakdown: BreakdownItem[]; penalty: number }

function scoreListing(L: Listing, hard: HardConstraints, cards: string[]): ScoreResult {
  if (hard.noBasement && L.floor < 1) return { excluded: true, reason: '반지하 제외' }
  if (hard.deposit && L.deposit > hard.deposit) return { excluded: true, reason: '보증금 초과' }
  if (hard.rent && L.rent > hard.rent + RENT_ALLOWANCE) return { excluded: true, reason: '월세 초과' }

  let sum = 0, wsum = 0
  const breakdown: BreakdownItem[] = cards.map(cid => {
    const c = CONDITION_CARDS[cid]
    const r = c.match(L)
    sum += c.weight * STATUS_VAL[r.status]
    wsum += c.weight
    return { cid, label: c.label, category: c.category, weight: c.weight, ...r }
  })
  let score = wsum ? (sum / wsum) * 100 : 0
  let penalty = 0
  if (hard.rent && L.rent > hard.rent) penalty = Math.round((L.rent - hard.rent) * 1.6)
  score = Math.max(0, Math.round(score - penalty))

  return { excluded: false, score, breakdown, penalty }
}

const THUMB_MAP: Record<string, string> = { '빌라': '🏠', '원룸': '🏡', '오피스텔': '🏢' }
const CARD_LABELS: Record<string, string> = {
  pests: '벌레 없음',
  mold: '곰팡이 없음',
  default_options: '기본 옵션',
  convenience_facilities: '편의 시설',
  extra_notes: '기타 조건',
}

const CARD_BREAKDOWN_LABEL: Record<string, string> = {
  pests: '생활환경',
  mold: '위생',
  default_options: '옵션',
  convenience_facilities: '편의',
  extra_notes: '기타',
}

const CARD_COLOR: Record<string, string> = {
  pests: '#22C55E',
  mold: '#3B82F6',
  default_options: '#8B5CF6',
  convenience_facilities: '#F59E0B',
  extra_notes: '#6B7280',
}

const CARD_ICON: Record<string, string> = {
  pests: 'shield',
  mold: 'droplets',
  default_options: 'settings',
  convenience_facilities: 'store',
  extra_notes: 'note',
}

const CONV_KEYWORDS: Array<{ keyword: string; name: string; icon: string; defaultMin: number }> = [
  { keyword: '편의점', name: '편의점', icon: 'store', defaultMin: 3 },
  { keyword: '마트', name: '마트', icon: 'shopping-cart', defaultMin: 5 },
  { keyword: '약국', name: '약국', icon: 'pill', defaultMin: 5 },
  { keyword: '카페', name: '카페', icon: 'coffee', defaultMin: 5 },
  { keyword: '병원', name: '병원', icon: 'hospital', defaultMin: 10 },
]

function agentToLocationAnalysis(item: AgentPropertyItem): LocationAnalysis {
  const combined = item.description + ' ' + item.address_detail

  const extractMin = (keyword: string, fallback: number): number => {
    const m = combined.match(new RegExp(`${keyword}[^.]*?(\\d+)분`))
    return m ? parseInt(m[1]) : fallback
  }

  const scoreBreakdown = item.soft_card_matches.map(m => ({
    label: CARD_BREAKDOWN_LABEL[m.card] ?? m.card,
    score: m.matched === true ? 90 : m.matched === 'partial' ? 60 : 30,
  }))

  const commute = {
    legs: [{ label: item.transit_station, minutes: item.transit_walk_min, type: 'walk' as const }],
    totalMinutes: item.transit_walk_min,
    transfers: 0,
    mainNote: item.address_detail,
  }

  const hasCctv = item.facilities.includes('CCTV')
  const isBasement = combined.includes('반지하') || combined.includes('지하')
  const hasGoodLight = combined.includes('채광') || combined.includes('햇볕') || combined.includes('조망')
  const hasNearby = combined.includes('편의점') || combined.includes('마트')

  const nightSafety: NightSafetyItem[] = [
    { icon: 'camera', label: 'CCTV 설치', detail: hasCctv ? '건물 입구 CCTV 확인' : '정보 없음', pass: hasCctv },
    { icon: 'sun', label: '채광/층수 양호', detail: isBasement ? '반지하 구조' : hasGoodLight ? '채광 양호' : '일반 층수', pass: !isBasement },
    { icon: 'store', label: '편의시설 근접', detail: hasNearby ? '편의점/마트 근거리' : '정보 없음', pass: hasNearby },
  ]

  const convenience: ConvenienceFacility[] = CONV_KEYWORDS
    .filter(c => combined.includes(c.keyword))
    .map(c => ({ name: c.name, walkMin: extractMin(c.keyword, c.defaultMin), icon: c.icon }))

  const basis: RecommendationBasis[] = item.soft_card_matches
    .filter(m => m.matched === true || m.matched === 'partial')
    .map(m => ({
      category: CARD_BREAKDOWN_LABEL[m.card] ?? m.card,
      color: CARD_COLOR[m.card] ?? '#6B7280',
      icon: CARD_ICON[m.card] ?? 'check',
      detail: m.evidence,
    }))

  const SKIP = new Set(['조건 없음', '추가 요구사항 없음', '정보 없음'])
  const pros = item.soft_card_matches
    .filter(m => m.matched === true && !SKIP.has(m.evidence))
    .map(m => m.evidence)
  const cons = item.soft_card_matches
    .filter(m => m.matched === false && !SKIP.has(m.evidence))
    .map(m => m.evidence)

  const aiComment = `${item.title}은(는) ${item.location}에 위치합니다. ${item.description.slice(0, 80)}${item.description.length > 80 ? '...' : ''}`

  return { commute, nightSafety, convenience, basis, pros, cons, aiComment, scoreBreakdown }
}

function agentToScoredListing(item: AgentPropertyItem): ScoredListing {
  const matchToStatus = (matched: boolean | 'partial'): Status =>
    matched === true ? 'full' : matched === 'partial' ? 'partial' : 'none'

  const listing: Listing = {
    id: item.property_id,
    name: item.title,
    type: item.type,
    area: item.location,
    deposit: item.deposit,
    rent: item.monthly_rent,
    pyeong: 0,
    floor: 1,
    options: item.facilities,
    commuteMin: item.transit_walk_min,
    night: { lit: true, mainRoad: true, alleyM: 0 },
    nightTransit: 'ok',
    thumb: THUMB_MAP[item.type] ?? '🏠',
    desc: item.description,
    locationAnalysis: agentToLocationAnalysis(item),
    lat: item.lat ?? undefined,
    lng: item.lng ?? undefined,
  }

  const breakdown: BreakdownItem[] = item.soft_card_matches.map(m => ({
    cid: m.card,
    label: CARD_LABELS[m.card] ?? m.card,
    category: 'soft',
    weight: 1,
    status: matchToStatus(m.matched),
    evidence: m.evidence,
  }))

  return { L: listing, excluded: false, score: item.score, breakdown, penalty: 0 }
}

interface AppState {
  turn: number
  hard: HardConstraints
  cards: string[]
  recommended: boolean
  lastTop: ScoredListing[] | null
  excludedCount: number
  messages: Message[]
  currentStep: number
  isTyping: boolean
  activeView: ActiveView
  selectedListingId: string | null
  toastMessage: string | null
  sessionId: string
  conditionsComplete: boolean
  agentConditions: AgentConditions | null
  agentListings: Listing[]
  advance: (displayText?: string) => void
  sendMessage: (text: string) => void
  runRecommendation: (advanceSteps: boolean) => void
  updateRent: (value: number) => void
  reset: () => void
  openAnalysis: (listingId: string) => void
  closeAnalysis: () => void
  showToast: (msg: string) => void
}

const useAppStore = create<AppState>((set, get) => ({
  turn: 0,
  hard: {},
  cards: [],
  recommended: false,
  lastTop: null,
  excludedCount: 0,
  messages: [{ role: 'ai', text: GREETING }],
  currentStep: 1,
  isTyping: false,
  activeView: 'chat',
  selectedListingId: null,
  toastMessage: null,
  sessionId: `session_${Date.now()}`,
  conditionsComplete: false,
  agentConditions: null,
  agentListings: [],

  advance(displayText?: string) {
    const msg = (displayText ?? '').trim()
    if (!msg) return

    set(s => ({ messages: [...s.messages, { role: 'user', text: msg }], isTyping: true }))

    void postMessage(msg, get().sessionId).then(result => {
      const { monthly_rent, location_transport } = result.hard_conditions
      const { basement } = result.soft_conditions

      set(s => {
        const newHard: HardConstraints = { ...s.hard }
        if (monthly_rent.max_manwon !== null) newHard.rent = monthly_rent.max_manwon
        if (location_transport.commute_time_max_minutes !== null) newHard.commuteMax = location_transport.commute_time_max_minutes
        if (basement.avoid === true) newHard.noBasement = true

        const addCards: string[] = []
        if (monthly_rent.max_manwon !== null && !s.cards.includes('budget_75')) addCards.push('budget_75')
        if (location_transport.commute_time_max_minutes !== null && !s.cards.includes('gangnam_commute')) addCards.push('gangnam_commute')
        if (basement.avoid === true && !s.cards.includes('no_basement')) addCards.push('no_basement')

        return {
          hard: newHard,
          cards: [...s.cards, ...addCards],
          isTyping: false,
          agentConditions: result,
          conditionsComplete: result.missing_required_conditions.length === 0,
          messages: [...s.messages, { role: 'ai', text: result.next_question }],
        }
      })
    }).catch(() => {
      set(s => ({
        isTyping: false,
        messages: [...s.messages, {
          role: 'ai' as const,
          text: '서버에 연결할 수 없어요. 백엔드가 실행 중인지 확인해주세요.',
        }],
      }))
    })
  },

  sendMessage(text: string) {
    get().advance(text)
  },

  runRecommendation(advanceSteps: boolean) {
    const { agentConditions, sessionId, hard, cards } = get()

    const runLocal = () => {
      const scored = LISTINGS.map(L => ({ L, ...scoreListing(L, hard, cards) }))
      const ok = scored
        .filter((s): s is { L: Listing } & Extract<ScoreResult, { excluded: false }> => !s.excluded)
        .sort((a, b) => b.score - a.score)
      const top = ok.slice(0, 3)
      set({ lastTop: top, recommended: true, excludedCount: scored.length - ok.length })
      if (advanceSteps) {
        set({ currentStep: 2 })
        setTimeout(() => set({ currentStep: 3 }), 500)
      }
    }

    if (!agentConditions) {
      runLocal()
      return
    }

    set(s => ({
      messages: [
        ...s.messages,
        { role: 'ai' as const, text: '조건에 맞는 매물을 검색하고 있어요...', searching: true },
      ],
    }))

    void postRecommend(agentConditions, sessionId).then(response => {
      const top = response.top_properties.map(agentToScoredListing)
      set(s => ({
        messages: [
          ...s.messages.filter(m => !m.searching),
          { role: 'ai' as const, text: `맞춤 매물 TOP ${top.length}을 찾았어요. 우측에서 확인해보세요!` },
        ],
        lastTop: top,
        agentListings: top.map(sl => sl.L),
        recommended: true,
        excludedCount: 0,
      }))
      if (advanceSteps) {
        set({ currentStep: 2 })
        setTimeout(() => set({ currentStep: 3 }), 500)
      }
    }).catch(() => {
      set(s => ({ messages: s.messages.filter(m => !m.searching) }))
      runLocal()
    })
  },

  updateRent(value: number) {
    set(s => ({ hard: { ...s.hard, rent: value } }))
    get().runRecommendation(false)
  },

  reset() {
    set({
      turn: 0,
      hard: {},
      cards: [],
      recommended: false,
      lastTop: null,
      excludedCount: 0,
      messages: [{ role: 'ai', text: GREETING }],
      currentStep: 1,
      isTyping: false,
      activeView: 'chat',
      selectedListingId: null,
      toastMessage: null,
      sessionId: `session_${Date.now()}`,
      conditionsComplete: false,
      agentConditions: null,
      agentListings: [],
    })
  },

  openAnalysis(listingId: string) {
    set({ activeView: 'analysis', selectedListingId: listingId })
  },

  closeAnalysis() {
    set({ activeView: 'chat', selectedListingId: null })
  },

  showToast(msg: string) {
    set({ toastMessage: msg })
    setTimeout(() => set({ toastMessage: null }), 2600)
  },
}))

export default useAppStore
