import { Home, Check, RotateCcw } from 'lucide-react'
import useLiveStore from '../../store/useLiveStore'
import type { Stage } from '../../store/useLiveStore'

const STEPS: { key: Stage; label: string; target: string }[] = [
  { key: 'needs', label: '니즈 파악', target: 'sec-conditions' },
  { key: 'listings', label: '매물 추천', target: 'sec-recommendations' },
  { key: 'location', label: '입지 분석', target: 'sec-map' },
]

const ORDER: Record<Stage, number> = { needs: 0, listings: 1, location: 2 }

function scrollToSection(id: string): void {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'nearest' })
}

interface Props {
  started: boolean
}

export default function LiveTopBar({ started }: Props) {
  const stage = useLiveStore(s => s.stage)
  const reset = useLiveStore(s => s.reset)
  const cur = ORDER[stage]

  return (
    <header className="topbar">
      <button className="brand" type="button" onClick={() => void reset()} aria-label="홈으로">
        <div className="brand-mark"><Home size={21} strokeWidth={2.5} /></div>
        <div className="brand-text">
          <span className="brand-name">RoomPilot</span>
          <span className="brand-tag">AI 주거 코치 · 부산대 자취방</span>
        </div>
      </button>

      {started ? (
        <nav className="stepper" aria-label="에이전트 진행 단계">
        {STEPS.map((step, i) => {
          const state = i < cur ? 'done' : i === cur ? 'active' : 'waiting'
          const reachable = i <= cur
          return (
            <div key={step.key} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              {i > 0 && <span className={`stepper-line${i <= cur ? ' filled' : ''}`} />}
              <button
                type="button"
                className={`stepper-item ${state}${reachable ? ' reachable' : ''}`}
                onClick={() => reachable && scrollToSection(step.target)}
                disabled={!reachable}
                aria-label={`${step.label}${reachable ? ' 보기' : ' (대기 중)'}`}
              >
                <div className="stepper-dot">{state === 'done' ? <Check size={14} strokeWidth={3} /> : i + 1}</div>
                <div className="stepper-meta">
                  <span className="stepper-label">{step.label}</span>
                  <span className="stepper-state">
                    {state === 'done' ? '완료' : state === 'active' ? '진행 중' : '대기'}
                  </span>
                </div>
              </button>
            </div>
          )
        })}
        </nav>
      ) : (
        <span className="topbar-spacer" />
      )}

      <div className="topbar-actions">
        {started && (
          <button className="btn-ghost" onClick={() => void reset()} type="button">
            <RotateCcw size={14} /> 새 대화
          </button>
        )}
      </div>
    </header>
  )
}
