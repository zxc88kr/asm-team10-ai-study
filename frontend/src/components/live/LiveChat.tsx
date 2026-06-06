import type { KeyboardEvent } from 'react'
import { useRef, useEffect, useState } from 'react'
import { Bot, User, Send } from 'lucide-react'
import useLiveStore from '../../store/useLiveStore'

const PRIORITY_PRESETS: { label: string; order: string[] }[] = [
  { label: '안전 > 비용 > 통학', order: ['safety', 'budget', 'commute'] },
  { label: '비용 > 안전 > 통학', order: ['budget', 'safety', 'commute'] },
  { label: '통학 > 안전 > 비용', order: ['commute', 'safety', 'budget'] },
]

// 조건을 바꾸면 LangGraph 루프백 엣지가 매물·입지만 다시 흐른다(데모 시나리오 Scene 5).
const LOOPBACK_PRESETS = [
  '월세 5만 더 올리면 뭐가 달라져요?',
  '월세 5만 낮추면 어때요?',
  '보증금 500 더 쓸 수 있어요',
]

export default function LiveChat() {
  const { messages, busy, pending, error, send, answerPriority } = useLiveStore()
  const stage = useLiveStore(s => s.stage)
  const [inputVal, setInputVal] = useState('')
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, busy])

  const isPriority = pending?.questionType === 'edit_priority'
  const isDiscover = pending?.questionType === 'discover_question'

  const submit = (text: string) => {
    const msg = text.trim()
    if (!msg || busy || isPriority) return
    setInputVal('')
    void send(msg)
    inputRef.current?.focus()
  }

  const handleKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit(inputVal)
    }
  }

  return (
    <section className="chat">
      <div className="chat-head">
        <div className="chat-head-avatar"><Bot size={20} /></div>
        <div>
          <h1>AI 주거 코치와 대화</h1>
          <p>LangGraph 3-에이전트가 실시간으로 조건을 발굴·추천합니다</p>
        </div>
        <span className="live-pill"><span className="live-dot" /> LIVE</span>
      </div>

      <div className="chat-scroll" ref={scrollRef}>
        {messages.map((msg, i) => (
          <div key={i} className={`msg ${msg.role}`}>
            <div className={`avatar ${msg.role === 'ai' ? 'ai-av' : 'user-av'}`}>
              {msg.role === 'ai' ? <Bot size={16} /> : <User size={16} />}
            </div>
            <div className="bubble">{msg.text}</div>
          </div>
        ))}

        {busy && (
          <div className="msg ai typing">
            <div className="avatar ai-av"><Bot size={16} /></div>
            <div className="bubble"><span className="dot" /><span className="dot" /><span className="dot" /></div>
          </div>
        )}
        {error && (
          <div className="msg ai">
            <div className="avatar ai-av"><Bot size={16} /></div>
            <div className="bubble error">
              백엔드 연결 오류: {error} — 백엔드(uvicorn :8000)가 떠 있는지 확인해 주세요.
            </div>
          </div>
        )}
      </div>

      <div className="composer">
        {isPriority && !busy && (
          <div className="starter">
            <div className="starter-hint">안전·비용·통학이 부딪히면 무엇을 먼저 챙길까요?</div>
            <div className="quick">
              {PRIORITY_PRESETS.map(p => (
                <button key={p.label} className="chip priority" type="button" onClick={() => void answerPriority(p.order)}>
                  {p.label}
                </button>
              ))}
            </div>
          </div>
        )}
        {stage !== 'needs' && !isPriority && !isDiscover && !busy && (
          <div className="starter">
            <div className="starter-hint">조건을 바꿔 다시 추천받기 (루프백)</div>
            <div className="quick">
              {LOOPBACK_PRESETS.map(p => (
                <button key={p} className="chip loop" type="button" onClick={() => submit(p)}>
                  {p}
                </button>
              ))}
            </div>
          </div>
        )}
        <div className="composer-row">
          <input
            ref={inputRef}
            className="chat-input"
            placeholder={
              isPriority ? '위 버튼으로 우선순위를 골라 주세요'
                : isDiscover ? '편하게 답해 주세요 (예: 어두운 골목은 좀 무서워요)'
                  : '예: 부산대 신입, 보증금 1000 월세 50'
            }
            value={inputVal}
            onChange={e => setInputVal(e.target.value)}
            onKeyDown={handleKey}
            disabled={busy || isPriority}
          />
          <button className="send" onClick={() => submit(inputVal)} type="button" disabled={!inputVal.trim() || busy || isPriority} aria-label="보내기">
            <Send size={17} />
          </button>
        </div>
      </div>
    </section>
  )
}
