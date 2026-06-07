import type { AgentConditions, AgentRecommendResponse } from '../types'

const API_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://localhost:8000'

async function request<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`API error: ${res.status}`)
  return res.json() as Promise<T>
}

export function postMessage(message: string, sessionId: string): Promise<AgentConditions> {
  return request<AgentConditions>('/agent/message', { message, session_id: sessionId })
}

export function postReset(sessionId: string): Promise<AgentConditions> {
  return request<AgentConditions>('/agent/reset', { session_id: sessionId })
}

export function postRecommend(
  conditions: AgentConditions,
  sessionId: string,
  topN = 3,
): Promise<AgentRecommendResponse> {
  return request<AgentRecommendResponse>('/agent/recommend', {
    conditions,
    session_id: sessionId,
    top_n: topN,
    use_solar: true,
  })
}
