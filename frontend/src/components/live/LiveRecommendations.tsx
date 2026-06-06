import useLiveStore from '../../store/useLiveStore'
import type { LiveMatch, LiveStatus } from '../../api/types'

const STATUS: Record<LiveStatus, { mark: string; color: string }> = {
  full: { mark: '충족', color: '#16A34A' },
  partial: { mark: '보통', color: '#D97706' },
  none: { mark: '미흡', color: '#DC2626' },
}

interface LocAnalysis {
  commute?: { totalMinutes?: number; mainNote?: string }
  nightSafety?: { label: string; pass: boolean }[]
  pros?: string[]
  aiComment?: string
}

function scoreColor(score: number): string {
  if (score >= 70) return '#16A34A'
  if (score >= 45) return '#D97706'
  return '#DC2626'
}

export default function LiveRecommendations() {
  const ranked = useLiveStore(s => s.ranked)
  const listings = useLiveStore(s => s.listings)
  const cards = useLiveStore(s => s.cards)
  const location = useLiveStore(s => s.location)
  const selected = useLiveStore(s => s.selectedListing)

  const labelOf = (m: LiveMatch) => cards.find(c => c.id === m.cardId)?.label ?? m.cardId
  const loc = selected ? (location[selected] as unknown as LocAnalysis | undefined) : undefined

  return (
    <>
      <div className="card">
        <div className="card-head"><h2>추천 매물 TOP 3</h2></div>
        {ranked.length === 0 ? (
          <p style={{ fontSize: 12, color: 'var(--muted)', padding: '4px 0', lineHeight: 1.6 }}>
            니즈 대화가 끝나면 의미 기반 매칭으로 맞춤 매물을 추천해드려요.
          </p>
        ) : (
          <ul className="rec-list">
            {ranked.map((sl, idx) => {
              const L = listings[sl.listingId]
              const hits = sl.breakdown.filter(b => b.status !== 'none').slice(0, 4)
              return (
                <li key={sl.listingId} className={`rec-item${idx === 0 ? ' top1' : ''}`}>
                  <div className={`rank-badge${idx === 0 ? ' gold' : ''}`}>{idx + 1}</div>
                  <div className="rec-body">
                    <div className="rec-name">{L?.name ?? sl.listingId}</div>
                    <div className="rec-meta">{L ? `${L.area} · 보 ${L.deposit} / 월 ${L.rent}만 원` : ''}</div>
                    <div className="rec-tags" style={{ flexWrap: 'wrap', gap: 4 }}>
                      {hits.map(b => (
                        <span key={b.cardId} className="rec-tag" style={{ color: STATUS[b.status].color }} title={b.evidence}>
                          {labelOf(b)} {STATUS[b.status].mark}
                        </span>
                      ))}
                    </div>
                    {sl.tradeoff && <div style={{ fontSize: 11, color: 'var(--muted)', marginTop: 4 }}>⚖ {sl.tradeoff}</div>}
                  </div>
                  <div className="score-badge" style={{ background: scoreColor(sl.score) }}>
                    {sl.score}<span>적합도</span>
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </div>

      {loc && selected && (
        <div className="card">
          <div className="card-head"><h2>입지 해설 · {listings[selected]?.name ?? selected}</h2></div>
          <div style={{ fontSize: 12, lineHeight: 1.7 }}>
            {loc.commute?.totalMinutes != null && <div>🎓 통학 약 {loc.commute.totalMinutes}분 · {loc.commute.mainNote}</div>}
            {(loc.nightSafety ?? []).map((n, i) => (
              <div key={i} style={{ color: n.pass ? 'var(--ink)' : '#DC2626' }}>{n.pass ? '🌙' : '⚠'} {n.label}</div>
            ))}
            {loc.aiComment && <div style={{ marginTop: 6, color: 'var(--muted)' }}>{loc.aiComment}</div>}
          </div>
        </div>
      )}
    </>
  )
}
