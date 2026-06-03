import { describe, it, expect, beforeEach, vi } from 'vitest'
import { act } from '@testing-library/react'
import useAppStore, { scoreClass, STATUS_KO } from '../useAppStore'

beforeEach(() => {
  act(() => useAppStore.getState().reset())
})

describe('초기 상태', () => {
  it('turn이 0으로 시작', () => {
    expect(useAppStore.getState().turn).toBe(0)
  })

  it('cards가 빈 배열로 시작', () => {
    expect(useAppStore.getState().cards).toEqual([])
  })

  it('messages에 AI 인사말이 있음', () => {
    const { messages } = useAppStore.getState()
    expect(messages).toHaveLength(1)
    expect(messages[0].role).toBe('ai')
  })

  it('currentStep이 1', () => {
    expect(useAppStore.getState().currentStep).toBe(1)
  })

  it('activeView가 chat으로 시작', () => {
    expect(useAppStore.getState().activeView).toBe('chat')
  })
})

describe('scoreClass', () => {
  it('85 이상 → sc-high', () => {
    expect(scoreClass(85)).toBe('sc-high')
    expect(scoreClass(100)).toBe('sc-high')
  })

  it('75~84 → sc-mid', () => {
    expect(scoreClass(75)).toBe('sc-mid')
    expect(scoreClass(80)).toBe('sc-mid')
  })

  it('75 미만 → sc-low', () => {
    expect(scoreClass(74)).toBe('sc-low')
    expect(scoreClass(0)).toBe('sc-low')
  })
})

describe('STATUS_KO', () => {
  it('full → 충족', () => expect(STATUS_KO.full).toBe('충족'))
  it('partial → 부분', () => expect(STATUS_KO.partial).toBe('부분'))
  it('none → 미흡', () => expect(STATUS_KO.none).toBe('미흡'))
})

describe('runRecommendation', () => {
  it('hard 제약 없이 실행하면 추천 목록이 채워짐', () => {
    act(() => useAppStore.getState().runRecommendation(false))
    const { lastTop, recommended } = useAppStore.getState()
    expect(recommended).toBe(true)
    expect(lastTop).not.toBeNull()
    expect(lastTop!.length).toBeGreaterThan(0)
  })

  it('월세 상한을 극단적으로 낮추면 excludedCount가 증가', () => {
    act(() => useAppStore.setState({ hard: { rent: 1 } }))
    act(() => useAppStore.getState().runRecommendation(false))
    expect(useAppStore.getState().excludedCount).toBeGreaterThan(0)
  })
})

describe('updateRent', () => {
  it('hard.rent 값을 업데이트', () => {
    act(() => useAppStore.getState().updateRent(50))
    expect(useAppStore.getState().hard.rent).toBe(50)
  })

  it('updateRent 후 추천이 갱신됨', () => {
    act(() => useAppStore.getState().updateRent(50))
    expect(useAppStore.getState().recommended).toBe(true)
  })
})

describe('showToast / toastMessage', () => {
  it('showToast 호출 후 toastMessage 설정됨', () => {
    vi.useFakeTimers()
    act(() => useAppStore.getState().showToast('테스트 메시지'))
    expect(useAppStore.getState().toastMessage).toBe('테스트 메시지')
    vi.useRealTimers()
  })
})

describe('openAnalysis / closeAnalysis', () => {
  it('openAnalysis 후 activeView가 analysis', () => {
    act(() => useAppStore.getState().openAnalysis('A'))
    expect(useAppStore.getState().activeView).toBe('analysis')
    expect(useAppStore.getState().selectedListingId).toBe('A')
  })

  it('closeAnalysis 후 activeView가 chat', () => {
    act(() => {
      useAppStore.getState().openAnalysis('A')
      useAppStore.getState().closeAnalysis()
    })
    expect(useAppStore.getState().activeView).toBe('chat')
    expect(useAppStore.getState().selectedListingId).toBeNull()
  })
})
