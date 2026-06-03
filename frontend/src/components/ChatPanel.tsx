import { useRef, useEffect, useState } from 'react'
import useAppStore from '../store/useAppStore'
import { SCENARIO } from '../data/scenario'

export default function ChatPanel() {
  const messages = useAppStore(s => s.messages)
  const isTyping = useAppStore(s => s.isTyping)
  const turn = useAppStore(s => s.turn)
  const advance = useAppStore(s => s.advance)
  const reset = useAppStore(s => s.reset)

  const [inputValue, setInputValue] = useState('')
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, isTyping])

  function handleSend() {
    const text = inputValue.trim()
    if (turn >= SCENARIO.length) {
      if (text) advance(text)
      setInputValue('')
      return
    }
    advance(text || undefined)
    setInputValue('')
  }

  const nextQuick = !isTyping && turn < SCENARIO.length ? SCENARIO[turn].userText : null

  return (
    <main className="chat">
      <header className="chat-head">
        <div>
          <h1>AI 주거 코치</h1>
          <p>조건·맥락을 이해해 집을 함께 찾아드려요</p>
        </div>
        <button className="btn-ghost" onClick={reset}>↻ 다시 시작</button>
      </header>

      <div className="chat-scroll" ref={scrollRef}>
        {messages.map((msg, i) => (
          <div key={i} className={`msg ${msg.role}`}>
            {msg.role === 'ai' && <div className="avatar">🤖</div>}
            <div className="bubble">{msg.text}</div>
          </div>
        ))}
        {isTyping && (
          <div className="msg ai typing">
            <div className="avatar">🤖</div>
            <div className="bubble">
              <span className="dot" />
              <span className="dot" />
              <span className="dot" />
            </div>
          </div>
        )}
      </div>

      <div className="composer">
        <div className="quick">
          {nextQuick && (
            <button className="chip" onClick={() => advance(nextQuick)}>
              {nextQuick}
            </button>
          )}
        </div>
        <div className="composer-row">
          <input
            className="chat-input"
            type="text"
            placeholder="메시지를 입력하거나 위 추천 답변을 눌러보세요…"
            autoComplete="off"
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
          />
          <button className="send" onClick={handleSend} aria-label="보내기">↑</button>
        </div>
      </div>
    </main>
  )
}
