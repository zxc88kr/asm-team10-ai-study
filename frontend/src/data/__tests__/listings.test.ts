import { describe, it, expect } from 'vitest'
import { LISTINGS } from '../listings'

describe('LISTINGS', () => {
  it('3개의 매물이 있음', () => {
    expect(LISTINGS).toHaveLength(3)
  })

  it('각 매물이 필수 필드를 모두 가짐', () => {
    const requiredFields = ['id', 'name', 'type', 'area', 'deposit', 'rent', 'pyeong', 'floor', 'options', 'commuteMin', 'night', 'nightTransit', 'thumb', 'desc', 'locationAnalysis']
    LISTINGS.forEach(listing => {
      requiredFields.forEach(field => {
        expect(listing, `매물 ${listing.id}에 ${field} 필드 없음`).toHaveProperty(field)
      })
    })
  })

  it('night 필드가 lit, mainRoad, alleyM을 가짐', () => {
    LISTINGS.forEach(listing => {
      expect(listing.night).toHaveProperty('lit')
      expect(listing.night).toHaveProperty('mainRoad')
      expect(listing.night).toHaveProperty('alleyM')
      expect(typeof listing.night.alleyM).toBe('number')
    })
  })

  it('nightTransit은 good | ok | poor 중 하나', () => {
    const valid = new Set(['good', 'ok', 'poor'])
    LISTINGS.forEach(listing => {
      expect(valid.has(listing.nightTransit), `매물 ${listing.id}의 nightTransit: ${listing.nightTransit}`).toBe(true)
    })
  })

  it('deposit과 rent는 양수', () => {
    LISTINGS.forEach(listing => {
      expect(listing.deposit).toBeGreaterThan(0)
      expect(listing.rent).toBeGreaterThan(0)
    })
  })

  it('id가 고유함', () => {
    const ids = LISTINGS.map(l => l.id)
    expect(new Set(ids).size).toBe(ids.length)
  })

  it('locationAnalysis에 scoreBreakdown이 있음', () => {
    LISTINGS.forEach(listing => {
      expect(listing.locationAnalysis.scoreBreakdown).toBeDefined()
      expect(listing.locationAnalysis.scoreBreakdown.length).toBeGreaterThan(0)
    })
  })
})
