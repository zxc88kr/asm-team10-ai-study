import { describe, it, expect, vi, beforeEach } from 'vitest'
import { postMessage, postReset } from '../agentApi'
import type { AgentConditions } from '../../types'

const EMPTY_CONDITIONS: AgentConditions = {
  session_id: 'default',
  hard_conditions: {
    location_transport: { areas: [], landmarks: [], commute_time_max_minutes: null, transport_notes: [] },
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
  missing_required_conditions: ['위치/교통', '월세'],
  next_question: '어느 지역이나 역 기준으로 찾고 싶으세요?',
}

function mockFetch(body: unknown, ok = true) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok,
      status: ok ? 200 : 500,
      json: () => Promise.resolve(body),
    }),
  )
}

beforeEach(() => {
  vi.restoreAllMocks()
})

describe('postMessage', () => {
  it('POST /agent/message 를 호출하고 응답을 반환', async () => {
    mockFetch(EMPTY_CONDITIONS)
    const result = await postMessage('강남역 근처 회사에 다녀요.', 'default')
    expect(result.session_id).toBe('default')
    expect(result.next_question).toBeTruthy()

    const calls = vi.mocked(fetch).mock.calls
    expect(calls).toHaveLength(1)
    const [url, init] = calls[0] as [string, { body: string }]
    expect(url).toContain('/agent/message')
    expect(JSON.parse(init.body)).toMatchObject({
      message: '강남역 근처 회사에 다녀요.',
      session_id: 'default',
    })
  })

  it('서버 에러 시 예외를 던짐', async () => {
    mockFetch({}, false)
    await expect(postMessage('test', 'default')).rejects.toThrow('API error: 500')
  })
})

describe('postReset', () => {
  it('POST /agent/reset 를 호출하고 응답을 반환', async () => {
    mockFetch(EMPTY_CONDITIONS)
    const result = await postReset('default')
    expect(result.session_id).toBe('default')

    const calls = vi.mocked(fetch).mock.calls
    const [url, init] = calls[0] as [string, { body: string }]
    expect(url).toContain('/agent/reset')
    expect(JSON.parse(init.body)).toMatchObject({ session_id: 'default' })
  })

  it('서버 에러 시 예외를 던짐', async () => {
    mockFetch({}, false)
    await expect(postReset('default')).rejects.toThrow('API error: 500')
  })
})
