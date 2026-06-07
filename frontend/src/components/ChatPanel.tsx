import type { KeyboardEvent } from 'react'
import { useRef, useEffect, useState } from 'react'
import { Bot, User, HelpCircle, Bell, RotateCcw, Paperclip, Mic, Send } from 'lucide-react'
import useAppStore from '../store/useAppStore'

function formatTime() {
  const now = new Date()
  const h = now.getHours()
  const m = now.getMinutes().toString().padStart(2, '0')
  const ampm = h >= 12 ? '오후' : '오전'
  return `${ampm} ${h > 12 ? h - 12 : h}:${m}`
}

export default function ChatPanel() {
  const { messages, isTyping, advance, reset, conditionsComplete, recommended, runRecommendation } = useAppStore()
  const [inputVal, setInputVal] = useState('')
  const [currentTime] = useState(formatTime)
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const isComposingRef = useRef(false)

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, isTyping])

  const handleSend = (text?: string) => {
    if (isTyping) return
    const msg = text ?? inputVal.trim()
    if (!msg) return
    setInputVal('')
    advance(msg)
    inputRef.current?.focus()
  }

  const handleKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.nativeEvent.isComposing || e.keyCode === 229 || isComposingRef.current) {
      return
    }

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
            <p>대화로 조건을 파악하고 맞춤 매물을 추천합니다</p>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <button className="btn-icon" type="button" aria-label="도움말"><HelpCircle size={15} /></button>
          <button className="btn-icon" type="button" aria-label="알림"><Bell size={15} /></button>
          <button className="btn-icon" onClick={reset} type="button">
            <RotateCcw size={13} /> 초기화
          </button>
        </div>
      </div>

      <div className="chat-scroll" ref={scrollRef}>
        {messages.map((msg, i) => (
          <div key={i} className={`msg ${msg.role}`}>
            {msg.role === 'ai' && <div className="avatar"><Bot size={20} /></div>}
            {msg.role === 'user' && <div className="avatar user-av"><User size={20} /></div>}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 3, maxWidth: '100%' }}>
              {msg.searching ? (
                <div className="searching-bubble">
                  <div className="search-spinner" />
                  <div style={{ flex: 1 }}>
                    <div style={{ marginBottom: 6 }}>{msg.text}</div>
                    <div className="search-bar-wrap">
                      <div className="search-bar-fill" />
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bubble">{msg.text}</div>
              )}
              <span className="msg-time">{currentTime}</span>
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="msg ai typing">
            <div className="avatar"><Bot size={20} /></div>
            <div className="bubble">
              <span className="dot" />
              <span className="dot" />
              <span className="dot" />
            </div>
          </div>
        )}
      </div>

      <div className="composer">
        {conditionsComplete && !recommended && !isTyping && (
          <div className="quick">
            <button
              className="chip"
              onClick={() => runRecommendation(true)}
              type="button"
            >
              매물 찾기
            </button>
          </div>
        )}
        <div className="composer-row">
          <button className="btn-icon" style={{ borderRadius: 20, padding: '8px 10px' }} type="button" aria-label="파일 첨부">
            <Paperclip size={15} />
          </button>
          <button className="btn-icon" style={{ borderRadius: 20, padding: '8px 10px' }} type="button" aria-label="음성 입력">
            <Mic size={15} />
          </button>
          <input
            ref={inputRef}
            className="chat-input"
            placeholder="예: 강남역 35분 이내, 월 75만원 이하"
            value={inputVal}
            onChange={e => setInputVal(e.target.value)}
            onKeyDown={handleKey}
            onCompositionStart={() => { isComposingRef.current = true }}
            onCompositionEnd={() => { isComposingRef.current = false }}
          />
          <button
            className="send"
            onClick={() => handleSend()}
            type="button"
            disabled={!inputVal.trim() || isTyping}
            aria-label="보내기"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  )
}
