// RoomPilot 백엔드 SSE 클라이언트. EventSource 는 GET 전용이라 fetch+ReadableStream 으로 파싱.

import type { LiveEvent, LiveListing } from './types'

const BASE: string = import.meta.env.VITE_API_BASE ?? 'http://127.0.0.1:8000'

export async function createSession(): Promise<string> {
  const res = await fetch(`${BASE}/session`, { method: 'POST' })
  if (!res.ok) throw new Error(`session 생성 실패 (${res.status})`)
  const data = (await res.json()) as { session_id: string }
  return data.session_id
}

export async function fetchListings(): Promise<LiveListing[]> {
  const res = await fetch(`${BASE}/listings`)
  if (!res.ok) throw new Error(`listings 조회 실패 (${res.status})`)
  const data = (await res.json()) as { listings: LiveListing[] }
  return data.listings
}

export async function streamMessage(
  sid: string,
  text: string,
  onEvent: (e: LiveEvent) => void,
): Promise<void> {
  await postSSE(`${BASE}/session/${sid}/message`, { text }, onEvent)
}

export async function streamResume(
  sid: string,
  payload: unknown,
  onEvent: (e: LiveEvent) => void,
): Promise<void> {
  await postSSE(`${BASE}/session/${sid}/resume`, { payload }, onEvent)
}

async function postSSE(
  url: string,
  body: unknown,
  onEvent: (e: LiveEvent) => void,
): Promise<void> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok || !res.body) throw new Error(`요청 실패 (${res.status})`)

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const chunks = buffer.split('\n\n')
    buffer = chunks.pop() ?? ''
    for (const chunk of chunks) emitFromChunk(chunk, onEvent)
  }
  if (buffer.trim()) emitFromChunk(buffer, onEvent)
}

function emitFromChunk(chunk: string, onEvent: (e: LiveEvent) => void): void {
  for (const line of chunk.split('\n')) {
    if (!line.startsWith('data:')) continue
    const json = line.slice(5).trim()
    if (!json) continue
    try {
      onEvent(JSON.parse(json) as LiveEvent)
    } catch {
      /* keep-alive/주석 라인 등은 무시 */
    }
  }
}
