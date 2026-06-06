import { ListChecks } from 'lucide-react'
import useLiveStore from '../../store/useLiveStore'
import type { LiveSource } from '../../api/types'

const SRC: Record<LiveSource, { bg: string; color: string; label: string }> = {
  said: { bg: 'var(--primary-soft)', color: 'var(--primary)', label: '직접' },
  extracted: { bg: 'var(--green-soft)', color: 'var(--green)', label: '추출' },
  discovered: { bg: 'var(--amber-soft)', color: 'var(--amber)', label: '발굴' },
}

export default function LiveConditions() {
  const cards = useLiveStore(s => s.cards)

  return (
    <div className="card" id="sec-conditions">
      <div className="card-head">
        <span className="head-ic"><ListChecks size={17} /></span>
        <h2>내 조건 카드</h2>
        {cards.length > 0 && (
          <span className="head-badge" style={{ background: 'var(--surface-2)', color: 'var(--ink-2)' }}>
            {cards.length}개
          </span>
        )}
      </div>

      {cards.length === 0 ? (
        <p className="empty-hint">대화를 시작하면 조건 카드가 실시간으로 채워집니다.</p>
      ) : (
        <div className="cond-rows">
          {cards.map(c => {
            const src = SRC[c.source]
            return (
              <div key={c.id} className="cond-row">
                <span className="src-tag" style={{ background: src.bg, color: src.color }}>{src.label}</span>
                <div className="cond-main">
                  <div className="cond-label">
                    {c.label}
                    {c.kind === 'soft' && c.weight >= 3 && <span className="cond-star">★</span>}
                  </div>
                  <div className="cond-reason">{c.reason}</div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
