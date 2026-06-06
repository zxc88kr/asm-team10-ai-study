import { Building2, MapPin, ChevronRight, Heart } from 'lucide-react'
import useLiveStore from '../../store/useLiveStore'
import type { LiveMatch, LiveStatus } from '../../api/types'

const STATUS: Record<LiveStatus, { mark: string; bg: string; color: string }> = {
  full: { mark: '충족', bg: 'var(--green-soft)', color: 'var(--green)' },
  partial: { mark: '보통', bg: 'var(--amber-soft)', color: 'var(--amber)' },
  none: { mark: '미흡', bg: 'var(--red-soft)', color: 'var(--red)' },
}

interface LocAnalysis {
  commute?: { totalMinutes?: number; mainNote?: string }
  nightSafety?: { label: string; pass: boolean }[]
  pros?: string[]
  aiComment?: string
}

function scoreColor(score: number): string {
  if (score >= 70) return 'var(--green)'
  if (score >= 45) return 'var(--amber)'
  return 'var(--red)'
}

interface Props {
  onOpen: (id: string) => void
}

export default function LiveRecommendations({ onOpen }: Props) {
  const ranked = useLiveStore(s => s.ranked)
  const listings = useLiveStore(s => s.listings)
  const cards = useLiveStore(s => s.cards)
  const location = useLiveStore(s => s.location)
  const selected = useLiveStore(s => s.selectedListing)
  const favorites = useLiveStore(s => s.favorites)
  const toggleFavorite = useLiveStore(s => s.toggleFavorite)

  const labelOf = (m: LiveMatch) => cards.find(c => c.id === m.cardId)?.label ?? m.cardId
  const loc = selected ? (location[selected] as unknown as LocAnalysis | undefined) : undefined

  return (
    <>
      <div className="card" id="sec-recommendations">
        <div className="card-head">
          <span className="head-ic"><Building2 size={17} /></span>
          <h2>추천 매물 TOP 3</h2>
        </div>
        {ranked.length === 0 ? (
          <p className="empty-hint">
            니즈 대화가 끝나면 의미 기반 매칭으로 맞춤 매물을 추천해드려요.
          </p>
        ) : (
          <ul className="rec-list">
            {ranked.map((sl, idx) => {
              const L = listings[sl.listingId]
              const hits = sl.breakdown.filter(b => b.status !== 'none').slice(0, 4)
              const color = scoreColor(sl.score)
              return (
                <li
                  key={sl.listingId}
                  className={`rec-item clickable${idx === 0 ? ' top1' : ''}`}
                  onClick={() => onOpen(sl.listingId)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onOpen(sl.listingId) } }}
                >
                  <div className={`rank-chip${idx === 0 ? ' gold' : ''}`}>{idx + 1}</div>
                  <button
                    type="button"
                    className={`fav-heart${favorites.includes(sl.listingId) ? ' on' : ''}`}
                    onClick={e => { e.stopPropagation(); toggleFavorite(sl.listingId) }}
                    aria-label="찜하기"
                  >
                    <Heart size={15} fill={favorites.includes(sl.listingId) ? 'currentColor' : 'none'} />
                  </button>
                  <div className="rec-body">
                    <div className="rec-top">
                      <span className="rec-name">{L?.name ?? sl.listingId}</span>
                      <span className="rec-score" style={{ color }}>{sl.score}<small>점</small></span>
                    </div>
                    <div className="rec-meta">{L ? `${L.area} · 보 ${L.deposit} / 월 ${L.rent}만 원` : ''}</div>
                    <div className="rec-tags">
                      {hits.map(b => {
                        const st = STATUS[b.status]
                        return (
                          <span key={b.cardId} className="rec-tag" style={{ background: st.bg, color: st.color }} title={b.evidence}>
                            {labelOf(b)} {st.mark}
                          </span>
                        )
                      })}
                    </div>
                    {sl.tradeoff && <div className="rec-tradeoff">⚖ {sl.tradeoff}</div>}
                    <div className="score-track">
                      <span className="score-track-fill" style={{ width: `${Math.min(sl.score, 100)}%`, background: color }} />
                    </div>
                    <div className="rec-more">상세 · 지도 보기 <ChevronRight size={13} /></div>
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </div>

      {loc && selected && (
        <div className="card">
          <div className="card-head">
            <span className="head-ic"><MapPin size={17} /></span>
            <h2>입지 해설 · {listings[selected]?.name ?? selected}</h2>
          </div>
          <div className="loc-rows">
            {loc.commute?.totalMinutes != null && (
              <div className="loc-row"><span className="loc-ic ok">🎓</span><span>통학 약 {loc.commute.totalMinutes}분 · {loc.commute.mainNote}</span></div>
            )}
            {(loc.nightSafety ?? []).map((n, i) => (
              <div key={i} className="loc-row">
                <span className={`loc-ic ${n.pass ? 'ok' : 'warn'}`}>{n.pass ? '🌙' : '⚠'}</span>
                <span style={{ color: n.pass ? 'var(--ink)' : 'var(--red)' }}>{n.label}</span>
              </div>
            ))}
          </div>
          {loc.aiComment && <div className="loc-comment">{loc.aiComment}</div>}
        </div>
      )}
    </>
  )
}
