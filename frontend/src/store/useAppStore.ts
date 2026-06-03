import { create } from 'zustand'
import { SCENARIO, GREETING } from '../data/scenario'
import { CONDITION_CARDS } from '../data/conditions'
import { LISTINGS } from '../data/listings'
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

const END_MSG = '이 프로토타입의 시나리오는 여기까지예요. 오른쪽에서 추천 매물을 확인하거나 조건을 수정해 보세요 🙂'

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

  advance(displayText?: string) {
    const { turn } = get()

    if (turn >= SCENARIO.length) {
      if (!displayText) return
      set(s => ({ messages: [...s.messages, { role: 'user', text: displayText }], isTyping: true }))
      setTimeout(() => {
        set(s => ({ isTyping: false, messages: [...s.messages, { role: 'ai', text: END_MSG }] }))
      }, 650)
      return
    }

    const step = SCENARIO[turn]
    const userMsg = displayText || step.userText

    set(s => ({ messages: [...s.messages, { role: 'user', text: userMsg }], isTyping: true }))

    if (step.hard) {
      set(s => ({ hard: { ...s.hard, ...step.hard } }))
    }

    ;(step.cards || []).forEach((cid, i) => {
      setTimeout(() => {
        set(s => s.cards.includes(cid) ? {} : { cards: [...s.cards, cid] })
      }, 300 + i * 260)
    })

    set(s => ({ turn: s.turn + 1 }))

    setTimeout(() => {
      if (step.recommend) {
        set(s => ({
          isTyping: false,
          messages: [...s.messages, { role: 'ai', text: step.aiText, searching: true }],
        }))
        setTimeout(() => get().runRecommendation(true), 1200)
      } else {
        set(s => ({ isTyping: false, messages: [...s.messages, { role: 'ai', text: step.aiText }] }))
      }
    }, 650)
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
