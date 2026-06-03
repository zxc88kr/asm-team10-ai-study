import { describe, it, expect } from 'vitest'
import { CONDITION_CARDS, CATEGORY_CLASS } from '../conditions'
import type { Listing } from '../../types'

const BASE_LOCATION_ANALYSIS: Listing['locationAnalysis'] = {
  commute: { legs: [], totalMinutes: 20, transfers: 0, mainNote: '' },
  nightSafety: [],
  convenience: [],
  basis: [],
  pros: [],
  cons: [],
  aiComment: '',
  scoreBreakdown: [],
}

const makeListingBase = (overrides: Partial<Listing> = {}): Listing => ({
  id: 'TEST', name: '테스트 매물', type: '원룸', area: '강남',
  deposit: 1000, rent: 70, pyeong: 7, floor: 3,
  commuteMin: 20,
  options: ['풀옵션', '에어컨', '세탁기'],
  night: { lit: true, mainRoad: true, alleyM: 50 },
  nightTransit: 'ok',
  thumb: '🏠',
  desc: '남향 채광 좋고 환기 잘 됩니다.',
  locationAnalysis: BASE_LOCATION_ANALYSIS,
  ...overrides,
})

describe('gangnam_commute', () => {
  const card = CONDITION_CARDS.gangnam_commute

  it('commuteMin 20 이하 → full', () => {
    const result = card.match(makeListingBase({ commuteMin: 15 }))
    expect(result.status).toBe('full')
    expect(result.evidence).toContain('15분')
  })

  it('commuteMin 21~35 → partial', () => {
    const result = card.match(makeListingBase({ commuteMin: 30 }))
    expect(result.status).toBe('partial')
  })

  it('commuteMin 36 이상 → none', () => {
    const result = card.match(makeListingBase({ commuteMin: 40 }))
    expect(result.status).toBe('none')
  })
})

describe('budget_75', () => {
  const card = CONDITION_CARDS.budget_75

  it('rent 75 이하 → full', () => {
    const result = card.match(makeListingBase({ rent: 75 }))
    expect(result.status).toBe('full')
  })

  it('rent 76~80 → partial', () => {
    const result = card.match(makeListingBase({ rent: 78 }))
    expect(result.status).toBe('partial')
  })

  it('rent 81 이상 → none', () => {
    const result = card.match(makeListingBase({ rent: 85 }))
    expect(result.status).toBe('none')
  })
})

describe('no_basement', () => {
  const card = CONDITION_CARDS.no_basement

  it('floor >= 1 → full', () => {
    const result = card.match(makeListingBase({ floor: 3 }))
    expect(result.status).toBe('full')
  })

  it('floor 0 이하 → none', () => {
    const result = card.match(makeListingBase({ floor: 0 }))
    expect(result.status).toBe('none')
  })
})

describe('night_safe', () => {
  const card = CONDITION_CARDS.night_safe

  it('가로등·큰길·골목 100m 이하 → full', () => {
    const result = card.match(makeListingBase({ night: { lit: true, mainRoad: true, alleyM: 90 } }))
    expect(result.status).toBe('full')
  })

  it('큰길 없음, 가로등만 → partial', () => {
    const result = card.match(makeListingBase({ night: { lit: true, mainRoad: false, alleyM: 150 } }))
    expect(result.status).toBe('partial')
  })

  it('가로등·큰길 모두 없음 → none', () => {
    const result = card.match(makeListingBase({ night: { lit: false, mainRoad: false, alleyM: 200 } }))
    expect(result.status).toBe('none')
  })
})

describe('night_transit', () => {
  const card = CONDITION_CARDS.night_transit

  it('good → full', () => {
    expect(card.match(makeListingBase({ nightTransit: 'good' })).status).toBe('full')
  })

  it('ok → partial', () => {
    expect(card.match(makeListingBase({ nightTransit: 'ok' })).status).toBe('partial')
  })

  it('poor → none', () => {
    expect(card.match(makeListingBase({ nightTransit: 'poor' })).status).toBe('none')
  })
})

describe('CATEGORY_CLASS', () => {
  it('모든 카테고리에 CSS 클래스가 정의됨', () => {
    const categories = ['안전', '비용', '출퇴근', '구조', '편의']
    categories.forEach(cat => {
      expect(CATEGORY_CLASS[cat]).toBeDefined()
      expect(typeof CATEGORY_CLASS[cat]).toBe('string')
    })
  })
})
