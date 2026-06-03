import { describe, it, expect } from 'vitest'
import { CONDITION_CARDS, CATEGORY_CLASS } from '../conditions'
import type { Listing } from '../../types'

const makeListingBase = (overrides: Partial<Listing> = {}): Listing => ({
  id: 'TEST', name: '테스트 매물', type: '원룸', area: '신촌',
  deposit: 1000, rent: 50, pyeong: 7, floor: 3,
  walkMin: 10,
  options: ['풀옵션', '에어컨', '세탁기'],
  night: { lit: true, mainRoad: true, alleyM: 50 },
  nightTransit: 'ok',
  thumb: '🏠',
  desc: '남향 채광 좋고 환기 잘 됩니다.',
  ...overrides,
})

describe('school_near', () => {
  const card = CONDITION_CARDS.school_near

  it('walkMin 15 이하 → full', () => {
    const result = card.match(makeListingBase({ walkMin: 10 }))
    expect(result.status).toBe('full')
    expect(result.evidence).toContain('10분')
  })

  it('walkMin 16~25 → partial', () => {
    const result = card.match(makeListingBase({ walkMin: 20 }))
    expect(result.status).toBe('partial')
  })

  it('walkMin 26 이상 → none', () => {
    const result = card.match(makeListingBase({ walkMin: 30 }))
    expect(result.status).toBe('none')
  })
})

describe('fulloption', () => {
  const card = CONDITION_CARDS.fulloption

  it('options에 풀옵션 포함 → full', () => {
    const result = card.match(makeListingBase({ options: ['풀옵션', '에어컨'] }))
    expect(result.status).toBe('full')
  })

  it('desc에 풀옵션 키워드 → full', () => {
    const result = card.match(makeListingBase({ options: [], desc: '가전 포함된 깔끔한 방' }))
    expect(result.status).toBe('full')
  })

  it('옵션 3개 이상이지만 풀옵션 미표기 → partial', () => {
    const result = card.match(makeListingBase({ options: ['에어컨', '세탁기', '냉장고'], desc: '' }))
    expect(result.status).toBe('partial')
  })

  it('옵션 2개 이하 → none', () => {
    const result = card.match(makeListingBase({ options: ['에어컨'], desc: '' }))
    expect(result.status).toBe('none')
  })
})

describe('safe_route', () => {
  const card = CONDITION_CARDS.safe_route

  it('가로등·큰길·골목 80m 이하 → full', () => {
    const result = card.match(makeListingBase({ night: { lit: true, mainRoad: true, alleyM: 60 } }))
    expect(result.status).toBe('full')
  })

  it('큰길 없음, 가로등만 → partial', () => {
    const result = card.match(makeListingBase({ night: { lit: true, mainRoad: false, alleyM: 100 } }))
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

describe('separated_vent', () => {
  const card = CONDITION_CARDS.separated_vent

  it('분리형 키워드 → full', () => {
    const result = card.match(makeListingBase({ desc: '분리형 구조로 환기 우수' }))
    expect(result.status).toBe('full')
  })

  it('키워드 2개 이상(분리형 제외) → full', () => {
    const result = card.match(makeListingBase({ desc: '채광 좋고 통풍이 잘 됨' }))
    expect(result.status).toBe('full')
  })

  it('키워드 1개 → partial', () => {
    // '남향'도 키워드이므로 '남향' 없이 채광 하나만 포함
    const result = card.match(makeListingBase({ desc: '채광이 좋은 깔끔한 방입니다.' }))
    expect(result.status).toBe('partial')
  })

  it('키워드 없음 → none', () => {
    const result = card.match(makeListingBase({ desc: '조용한 원룸입니다.' }))
    expect(result.status).toBe('none')
  })
})

describe('CATEGORY_CLASS', () => {
  it('모든 카테고리에 CSS 클래스가 정의됨', () => {
    const categories = ['안전', '비용', '통학', '구조', '편의']
    categories.forEach(cat => {
      expect(CATEGORY_CLASS[cat]).toBeDefined()
      expect(typeof CATEGORY_CLASS[cat]).toBe('string')
    })
  })
})
