import { describe, it, expect, beforeEach, vi } from 'vitest'
import { act } from '@testing-library/react'
import useAppStore, { scoreClass, STATUS_KO } from '../useAppStore'
import type { AgentConditions } from '../../types'
import { postMessage, postReset } from '../../services/agentApi'

vi.mock('../../services/agentApi', () => ({
  postMessage: vi.fn(),
  postReset: vi.fn(),
}))

const makeConditions = (overrides: Partial<AgentConditions> = {}): AgentConditions => ({
  session_id: 'default',
  hard_conditions: {
    location_transport: { areas: ['강남'], landmarks: ['강남역'], commute_time_max_minutes: null, transport_notes: [] },
    monthly_rent: { max_krw: null, max_manwon: null, includes_management_fee: null },
  },
  soft_conditions: {
    convenience_facilities: { required: [], preferred: [], notes: [] },
    pests: { avoid: null, evidence: [] },
    default_options: { required: [], preferred: [] },
    basement: { avoid: null, evidence: [] },
    mold: { avoid: null, evidence: [] },
    extra_notes: [],
  },
  missing_required_conditions: ['월세'],
  next_question: '월세는 최대 얼마까지 가능하세요?',
  ...overrides,
})

beforeEach(() => {
  vi.mocked(postReset).mockResolvedValue({} as AgentConditions)
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

describe('sendMessage', () => {
  it('유저 메시지와 AI 응답이 messages에 추가됨', async () => {
    vi.mocked(postMessage).mockResolvedValue(makeConditions())

    await act(async () => {
      await useAppStore.getState().sendMessage('강남역 근처 회사에 다녀요.')
    })

    const { messages } = useAppStore.getState()
    expect(messages.some(m => m.role === 'user' && m.text === '강남역 근처 회사에 다녀요.')).toBe(true)
    expect(messages.some(m => m.role === 'ai' && m.text === '월세는 최대 얼마까지 가능하세요?')).toBe(true)
  })

  it('agentConditions 가 업데이트됨', async () => {
    vi.mocked(postMessage).mockResolvedValue(makeConditions())

    await act(async () => {
      await useAppStore.getState().sendMessage('강남역 근처 회사에 다녀요.')
    })

    const { agentConditions } = useAppStore.getState()
    expect(agentConditions).not.toBeNull()
    expect(agentConditions?.hard_conditions.location_transport.landmarks).toContain('강남역')
  })

  it('hard.rent 가 max_manwon 으로 업데이트됨', async () => {
    vi.mocked(postMessage).mockResolvedValue(
      makeConditions({
        hard_conditions: {
          location_transport: { areas: [], landmarks: [], commute_time_max_minutes: null, transport_notes: [] },
          monthly_rent: { max_krw: 750000, max_manwon: 75, includes_management_fee: true },
        },
        missing_required_conditions: ['위치/교통'],
        next_question: '어느 지역이나 역 기준으로 찾고 싶으세요?',
      }),
    )

    await act(async () => {
      await useAppStore.getState().sendMessage('관리비 포함 75만 원 이하였으면 해요.')
    })

    expect(useAppStore.getState().hard.rent).toBe(75)
  })

  it('API 오류 시 에러 메시지가 추가됨', async () => {
    vi.mocked(postMessage).mockRejectedValue(new Error('API error: 500'))

    await act(async () => {
      await useAppStore.getState().sendMessage('테스트')
    })

    const { messages } = useAppStore.getState()
    expect(messages.some(m => m.role === 'ai' && m.text.includes('연결할 수 없어요'))).toBe(true)
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
