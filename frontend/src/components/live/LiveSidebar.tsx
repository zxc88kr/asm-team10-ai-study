import { Home, MessageCircle, Building2, MapPin, Check } from 'lucide-react'
import useLiveStore from '../../store/useLiveStore'
import type { Stage } from '../../store/useLiveStore'

const STEPS: { key: Stage; label: string }[] = [
  { key: 'needs', label: '니즈 파악' },
  { key: 'listings', label: '매물 추천' },
  { key: 'location', label: '입지 분석' },
]

const ORDER: Record<Stage, number> = { needs: 0, listings: 1, location: 2 }

export default function LiveSidebar() {
  const stage = useLiveStore(s => s.stage)
  const metric = useLiveStore(s => s.metric)
  const cur = ORDER[stage]

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark"><Home size={20} strokeWidth={2.5} /></div>
        <span className="brand-name">RoomPilot</span>
      </div>

      <nav className="nav">
        <button className="nav-item active" type="button"><span className="nav-ic"><MessageCircle size={18} /></span><span>대화</span></button>
        <button className="nav-item" type="button"><span className="nav-ic"><Building2 size={18} /></span><span>추천 매물</span></button>
        <button className="nav-item" type="button"><span className="nav-ic"><MapPin size={18} /></span><span>입지 분석</span></button>
      </nav>

      <div className="steps-section">
        <div className="steps-title">에이전트 진행</div>
        <ul className="step-list">
          {STEPS.map((step, i) => {
            const state = i < cur ? 'done' : i === cur ? 'active' : 'waiting'
            return (
              <li key={step.key} className={`step ${state === 'done' ? 'done' : state === 'active' ? 'active' : ''}`}>
                <div className="step-dot">{state === 'done' ? <Check size={14} strokeWidth={3} /> : i + 1}</div>
                <div className="step-text">
                  <span className="step-label">{step.label}</span>
                  <span className="step-status">{state === 'done' ? '완료' : state === 'active' ? '진행 중' : '대기 중'}</span>
                </div>
              </li>
            )
          })}
        </ul>
      </div>

      <div className="sidebar-foot">
        <div className="help-card">
          <div className="help-icon"><Home size={28} /></div>
          <div className="help-title">숨은 조건까지 발굴</div>
          <div className="help-desc">
            {metric
              ? `직접 말한 ${metric.said} : AI가 찾은 ${metric.derived} (${metric.ratio})`
              : '생활 대화만으로 AI가 숨은 주거 조건을 함께 찾아드려요.'}
          </div>
        </div>
      </div>
    </aside>
  )
}
