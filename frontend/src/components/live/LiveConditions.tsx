import useLiveStore from '../../store/useLiveStore'
import type { LiveSource } from '../../api/types'

const SRC: Record<LiveSource, { bg: string; color: string; label: string }> = {
  said: { bg: '#EEF3FF', color: '#4B7BF5', label: '🟦 직접' },
  extracted: { bg: '#DCFCE7', color: '#16A34A', label: '🟩 추출' },
  discovered: { bg: '#FEF3C7', color: '#D97706', label: '🟧 발굴' },
}

export default function LiveConditions() {
  const cards = useLiveStore(s => s.cards)
  const metric = useLiveStore(s => s.metric)

  return (
    <div className="card cond-summary">
      <div className="card-head">
        <h2>내 조건 요약</h2>
        {metric && metric.said > 0 && (
          <span
            style={{ fontSize: 12, fontWeight: 700, color: '#D97706', background: '#FEF3C7', padding: '3px 9px', borderRadius: 999 }}
            title={`직접 말한 ${metric.said} : AI가 발굴·연결한 ${metric.derived}`}
          >
            {metric.ratio}
          </span>
        )}
      </div>

      {cards.length === 0 ? (
        <p style={{ fontSize: 12, color: 'var(--muted)', padding: '4px 0' }}>대화를 통해 조건이 실시간으로 채워집니다.</p>
      ) : (
        <div className="cond-rows">
          {cards.map(c => {
            const src = SRC[c.source]
            return (
              <div key={c.id} className="cond-row" style={{ alignItems: 'flex-start' }}>
                <span style={{ fontSize: 10, fontWeight: 700, color: src.color, background: src.bg, padding: '2px 6px', borderRadius: 6, whiteSpace: 'nowrap', marginTop: 1 }}>
                  {src.label}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13, fontWeight: 600 }}>
                    {c.label}
                    {c.kind === 'soft' && c.weight >= 3 && <span style={{ color: '#D97706', marginLeft: 4 }}>★</span>}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--muted)', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {c.reason}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
