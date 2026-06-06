import type { KeyboardEvent } from 'react'
import { useRef, useState } from 'react'
import { ArrowRight, MessageSquareText, Building2, MapPin, Sparkles } from 'lucide-react'
import useLiveStore from '../../store/useLiveStore'

const STARTERS = [
  '부산대 신입인데 보증금 1000, 월세 50으로 보고 있어요',
  '밤 11시쯤 귀가하고 요리를 자주 해요',
  '학교까지 걸어서 갈 수 있으면 좋겠어요',
]

const FEATURES = [
  {
    icon: MessageSquareText,
    step: '01',
    title: '니즈 파악',
    desc: '생활 대화 속 말로 못 한 조건까지 AI가 발굴해 카드로 정리합니다.',
    example: '부산대 신입인데 보증금 1000, 월세 50으로 보고 있어요',
  },
  {
    icon: Building2,
    step: '02',
    title: '매물 추천',
    desc: '의미 기반 매칭으로 조건에 맞는 매물을 점수·근거와 함께 제시합니다.',
    example: '보증금 1000 월세 50, 부산대 근처 안전하고 가까운 원룸 추천해줘',
  },
  {
    icon: MapPin,
    step: '03',
    title: '입지 분석',
    desc: '통학 시간, 야간 안전 등 동네 맥락을 실거주 관점으로 해설합니다.',
    example: '밤 11시에 귀가하고 요리를 자주 해요. 안전한 동네면 좋겠어요',
  },
]

export default function LiveLanding() {
  const send = useLiveStore(s => s.send)
  const busy = useLiveStore(s => s.busy)
  const [value, setValue] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const submit = (text: string) => {
    const msg = text.trim()
    if (!msg || busy) return
    setValue('')
    void send(msg)
  }

  const fillExample = (text: string) => {
    setValue(text)
    inputRef.current?.focus()
    inputRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }

  const handleKey = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit(value)
    }
  }

  return (
    <section className="landing">
      <div className="landing-inner">
        <span className="eyebrow">
          <Sparkles size={13} /> 부산대 · 장전동 자취방 · LangGraph 3-에이전트
        </span>

        <h1 className="hero-title">
          말로 다 못 한 니즈까지,
          <br />
          <em>AI가 집 조건으로 번역합니다</em>
        </h1>

        <p className="hero-sub">
          예산과 지역만 알려주세요. 생활 대화 속 숨은 조건을 발굴해
          <br className="hero-br" /> 근거와 함께 딱 맞는 자취방을 추천해드립니다.
        </p>

        <div className="hero-input">
          <input
            ref={inputRef}
            className="hero-field"
            placeholder="예: 부산대 신입, 보증금 1000 월세 50, 밤늦게 귀가해요"
            value={value}
            onChange={e => setValue(e.target.value)}
            onKeyDown={handleKey}
            disabled={busy}
            aria-label="첫 메시지 입력"
          />
          <button
            className="hero-cta"
            type="button"
            onClick={() => submit(value)}
            disabled={!value.trim() || busy}
          >
            대화 시작 <ArrowRight size={17} />
          </button>
        </div>

        <div className="hero-starters">
          <span className="hero-starters-hint">이렇게 시작해보세요</span>
          <div className="hero-chips">
            {STARTERS.map(s => (
              <button key={s} className="hero-chip" type="button" onClick={() => submit(s)} disabled={busy}>
                {s}
              </button>
            ))}
          </div>
        </div>

        <div className="feature-grid">
          {FEATURES.map(f => {
            const Icon = f.icon
            return (
              <button
                key={f.step}
                type="button"
                className="feature-card"
                onClick={() => fillExample(f.example)}
                disabled={busy}
              >
                <div className="feature-top">
                  <span className="feature-ic"><Icon size={20} /></span>
                  <span className="feature-step">{f.step}</span>
                </div>
                <h3 className="feature-title">{f.title}</h3>
                <p className="feature-desc">{f.desc}</p>
                <span className="feature-cta">예시로 입력 채우기 <ArrowRight size={13} /></span>
              </button>
            )
          })}
        </div>
      </div>
    </section>
  )
}
