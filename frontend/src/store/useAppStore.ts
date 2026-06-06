import { create } from 'zustand'
import { GREETING } from '../data/scenario'
import { CONDITION_CARDS } from '../data/conditions'
import { LISTINGS } from '../data/listings'
import { postMessage } from '../services/agentApi'
import type { Listing, HardConstraints, Message, ScoredListing, Status, BreakdownItem, ActiveView } from '../types'

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
  advance: (displayText?: string) => void
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

  runRecommendation(advanceSteps: boolean) {
    const { hard, cards } = get()
    const scored = LISTINGS.map(L => ({ L, ...scoreListing(L, hard, cards) }))
    const ok = scored
      .filter((s): s is { L: Listing } & Extract<ScoreResult, { excluded: false }> => !s.excluded)
      .sort((a, b) => b.score - a.score)
    const top = ok.slice(0, 3)
    const excluded = scored.length - ok.length

    set({ lastTop: top, recommended: true, excludedCount: excluded })

    if (advanceSteps) {
      set({ currentStep: 2 })
      setTimeout(() => set({ currentStep: 3 }), 500)
    }
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
