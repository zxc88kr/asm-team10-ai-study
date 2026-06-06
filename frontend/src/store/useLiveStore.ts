import { create } from 'zustand'
import { createSession, fetchListings, streamMessage, streamResume } from '../api/client'
import type { LiveCard, LiveEvent, LiveListing, LiveLocation, LiveMetric, LiveQuestion, LiveRanked } from '../api/types'

const GREETING =
  '안녕하세요! AI 주거 코치 RoomPilot입니다. 부산대 근처 자취방을 찾고 계신가요?\n예산·지역을 알려주시면 대화로 숨은 조건까지 같이 찾아드릴게요.'

const FAV_KEY = 'roompilot.favorites'

function loadFavorites(): string[] {
  try {
    const raw = localStorage.getItem(FAV_KEY)
    return raw ? (JSON.parse(raw) as string[]) : []
  } catch {
    return []
  }
}

function saveFavorites(ids: string[]): void {
  try {
    localStorage.setItem(FAV_KEY, JSON.stringify(ids))
  } catch {
    /* localStorage 미지원 환경 무시 */
  }
}

export interface ChatMsg {
  role: 'ai' | 'user'
  text: string
}

export type Stage = 'needs' | 'listings' | 'location'

interface LiveState {
  sessionId: string | null
  ready: boolean
  busy: boolean
  error: string | null
  messages: ChatMsg[]
  cards: LiveCard[]
  metric: LiveMetric | null
  ranked: LiveRanked[]
  location: Record<string, LiveLocation>
  selectedListing: string | null
  listings: Record<string, LiveListing>
  stage: Stage
  pending: LiveQuestion | null
  favorites: string[]
  init: () => Promise<void>
  send: (text: string) => Promise<void>
  answerPriority: (order: string[]) => Promise<void>
  analyzeListing: (id: string) => Promise<void>
  toggleFavorite: (id: string) => void
  reset: () => Promise<void>
}

function reduce(s: LiveState, e: LiveEvent): Partial<LiveState> {
  switch (e.type) {
    case 'card': {
      const exists = s.cards.some(c => c.id === e.card.id)
      const cards = exists ? s.cards.map(c => (c.id === e.card.id ? e.card : c)) : [...s.cards, e.card]
      return { cards }
    }
    case 'metric':
      return { metric: { ratio: e.ratio, said: e.said, derived: e.derived } }
    case 'question': {
      const q: LiveQuestion = {
        questionType: e.questionType,
        category: e.category,
        text: e.text,
        categories: e.categories,
        options: e.options,
      }
      if (e.questionType === 'edit_priority') {
        return { pending: q, messages: [...s.messages, { role: 'ai', text: '거의 다 모였어요! 안전·비용·통학이 부딪히면 뭘 먼저 챙길까요? 우선순위를 정해 주세요.' }] }
      }
      if (e.text) return { pending: q, messages: [...s.messages, { role: 'ai', text: e.text }] }
      return { pending: q }
    }
    case 'ranked':
      return { ranked: e.ranked, stage: 'listings' }
    case 'location':
      return { location: { ...s.location, [e.listingId]: e.analysis as LiveLocation }, selectedListing: e.listingId, stage: 'location' }
    case 'message':
      return { messages: [...s.messages, { role: e.role, text: e.text }] }
    default:
      return {}
  }
}

const useLiveStore = create<LiveState>((set, get) => {
  const apply = (e: LiveEvent) => set(s => reduce(s, e))

  return {
    sessionId: null,
    ready: false,
    busy: false,
    error: null,
    messages: [],
    cards: [],
    metric: null,
    ranked: [],
    location: {},
    selectedListing: null,
    listings: {},
    stage: 'needs',
    pending: null,
    favorites: loadFavorites(),

    async init() {
      set({ busy: true, error: null })
      try {
        const [sid, listings] = await Promise.all([createSession(), fetchListings()])
        const map: Record<string, LiveListing> = {}
        listings.forEach(l => { map[l.id] = l })
        set({ sessionId: sid, listings: map, ready: true, messages: [{ role: 'ai', text: GREETING }] })
      } catch (err) {
        set({ error: err instanceof Error ? err.message : String(err) })
      } finally {
        set({ busy: false })
      }
    },

    async send(text: string) {
      const { sessionId, busy, pending } = get()
      if (!sessionId || busy || !text.trim()) return
      if (pending && pending.questionType === 'edit_priority') return // 우선순위는 버튼으로
      set(s => ({ messages: [...s.messages, { role: 'user', text }], busy: true, error: null }))
      try {
        if (pending && pending.questionType === 'discover_question') {
          set({ pending: null })
          await streamResume(sessionId, text, apply)
        } else {
          await streamMessage(sessionId, text, apply)
        }
      } catch (err) {
        set({ error: err instanceof Error ? err.message : String(err) })
      } finally {
        set({ busy: false })
      }
    },

    async answerPriority(order: string[]) {
      const { sessionId, busy } = get()
      if (!sessionId || busy) return
      set(s => ({
        pending: null,
        busy: true,
        error: null,
        messages: [...s.messages, { role: 'user', text: `우선순위: ${order.join(' > ')}` }],
      }))
      try {
        await streamResume(sessionId, { order }, apply)
      } catch (err) {
        set({ error: err instanceof Error ? err.message : String(err) })
      } finally {
        set({ busy: false })
      }
    },

    async analyzeListing(id: string) {
      const { listings, busy } = get()
      if (busy) return
      const name = listings[id]?.name ?? id
      await get().send(`${name} 입지 분석해줘`)
    },

    toggleFavorite(id: string) {
      set(s => {
        const favorites = s.favorites.includes(id)
          ? s.favorites.filter(f => f !== id)
          : [...s.favorites, id]
        saveFavorites(favorites)
        return { favorites }
      })
    },

    async reset() {
      set({
        messages: [], cards: [], metric: null, ranked: [], location: {},
        selectedListing: null, stage: 'needs', pending: null, error: null,
      })
      await get().init()
    },
  }
})

export default useLiveStore
