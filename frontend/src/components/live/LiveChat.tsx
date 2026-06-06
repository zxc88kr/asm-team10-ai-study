import type { KeyboardEvent } from 'react'
import { useRef, useEffect, useState } from 'react'
import { Bot, User, RotateCcw, Send } from 'lucide-react'
import useLiveStore from '../../store/useLiveStore'

const PRIORITY_PRESETS: { label: string; order: string[] }[] = [
  { label: '안전 > 비용 > 통학', order: ['safety', 'budget', 'commute'] },
  { label: '비용 > 안전 > 통학', order: ['budget', 'safety', 'commute'] },
  { label: '통학 > 안전 > 비용', order: ['commute', 'safety', 'budget'] },
]

export default function LiveChat() {
  const { messages, busy, pending, error, send, answerPriority, reset } = useLiveStore()
  const [inputVal, setInputVal] = useState('')
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, busy])

  const isPriority = pending?.questionType === 'edit_priority'
  const isDiscover = pending?.questionType === 'discover_question'

  const handleSend = () => {
    const msg = inputVal.trim()
    if (!msg || busy || isPriority) return
    setInputVal('')
    void send(msg)
    inputRef.current?.focus()
  }

  const handleKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="chat">
      <div className="chat-head">
        <div className="chat-head-left">
          <div className="chat-head-avatar"><Bot size={20} /></div>
          <div>
            <h1>AI 주거 코치</h1>
            <p>실시간 LangGraph 3-에이전트 · 대화로 숨은 조건까지</p>
          </div>
        </div>
        <button className="btn-icon" onClick={() => void reset()} type="button">
          <RotateCcw size={13} /> 초기화
        </button>
      </div>

      <div className="chat-scroll" ref={scrollRef}>
        {messages.map((msg, i) => (
          <div key={i} className={`msg ${msg.role}`}>
            {msg.role === 'ai' ? <div className="avatar"><Bot size={15} /></div> : <div className="avatar user-av"><User size={15} /></div>}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 3, maxWidth: '100%' }}>
              <div className="bubble" style={{ whiteSpace: 'pre-wrap' }}>{msg.text}</div>
            </div>
          </div>
        ))}

        {busy && (
          <div className="msg ai typing">
            <div className="avatar"><Bot size={15} /></div>
            <div className="bubble"><span className="dot" /><span className="dot" /><span className="dot" /></div>
          </div>
        )}
        {error && (
          <div className="msg ai">
            <div className="avatar"><Bot size={15} /></div>
            <div className="bubble" style={{ background: '#FEE2E2', color: '#DC2626' }}>
              백엔드 연결 오류: {error} — 백엔드(uvicorn :8000)가 떠 있는지 확인해 주세요.
            </div>
          </div>
        )}
      </div>

      <div className="composer">
        {isPriority && !busy && (
          <div className="quick">
            {PRIORITY_PRESETS.map(p => (
              <button key={p.label} className="chip" type="button" onClick={() => void answerPriority(p.order)}>
                {p.label}
              </button>
            ))}
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
          <button className="send" onClick={handleSend} type="button" disabled={!inputVal.trim() || busy || isPriority} aria-label="보내기">
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  )
}
