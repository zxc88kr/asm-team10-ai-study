import { useEffect, useState } from 'react'
import { X, MapPin, Train, Footprints, ShieldCheck, ShoppingBag, Check, AlertTriangle, Sparkles, Heart, Share2, Navigation, Loader, Database } from 'lucide-react'
import useLiveStore from '../../store/useLiveStore'
import LiveMap from './LiveMap'

const CAMPUS = '35.2332,129.0794' // 부산대 정문(데모 기준점)

const INFRA: { key: string; label: string }[] = [
  { key: 'convenience', label: '편의점' },
  { key: 'supermarket', label: '마트' },
  { key: 'cafe', label: '카페' },
  { key: 'pharmacy', label: '약국' },
  { key: 'hospital', label: '병원' },
  { key: 'police', label: '경찰' },
  { key: 'bus', label: '버스' },
]

interface Props {
  listingId: string
  onClose: () => void
  onSelect: (id: string) => void
}

function scoreColor(score: number): string {
  if (score >= 70) return 'var(--green)'
  if (score >= 45) return 'var(--amber)'
  return 'var(--red)'
}

export default function LiveListingModal({ listingId, onClose, onSelect }: Props) {
  const listing = useLiveStore(s => s.listings[listingId])
  const ranked = useLiveStore(s => s.ranked)
  const aiLoc = useLiveStore(s => s.location[listingId])
  const busy = useLiveStore(s => s.busy)
  const favorites = useLiveStore(s => s.favorites)
  const toggleFavorite = useLiveStore(s => s.toggleFavorite)
  const analyzeListing = useLiveStore(s => s.analyzeListing)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  if (!listing) return null

  const loc = listing.location ?? {}
  const aiComment = aiLoc?.aiComment ?? loc.aiComment
  const sl = ranked.find(r => r.listingId === listingId)
  const rankIdx = ranked.findIndex(r => r.listingId === listingId)
  const faved = favorites.includes(listingId)
  const hasRanked = ranked.length > 0
  const { lat, lng } = listing.geo
  const directionsUrl =
    typeof lat === 'number' && typeof lng === 'number'
      ? `https://www.openstreetmap.org/directions?engine=fossgis_osrm_foot&route=${CAMPUS}%3B${lat}%2C${lng}`
      : null

  const share = async () => {
    const text = `${listing.name} · ${listing.area} · 보증금 ${listing.deposit}만 / 월세 ${listing.rent}만 — RoomPilot 추천`
    try {
      if (typeof navigator.share === 'function') {
        await navigator.share({ title: listing.name, text })
      } else {
        await navigator.clipboard.writeText(text)
        setCopied(true)
        window.setTimeout(() => setCopied(false), 1800)
      }
    } catch {
      /* 사용자가 공유 취소 */
    }
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={e => e.stopPropagation()} role="dialog" aria-modal="true" aria-label={`${listing.name} 상세`}>
        <button className="modal-close" type="button" onClick={onClose} aria-label="닫기"><X size={18} /></button>

        <div className="modal-head">
          <div>
            <div className="modal-title-row">
              {rankIdx >= 0 && <span className={`rank-chip${rankIdx === 0 ? ' gold' : ''}`}>{rankIdx + 1}</span>}
              <h2 className="modal-title">{listing.name}</h2>
            </div>
            <p className="modal-sub">{listing.type} · {listing.area} · {listing.pyeong}평 · {listing.floor}층</p>
          </div>
          {sl && <span className="modal-score" style={{ color: scoreColor(sl.score) }}>{sl.score}<small>점</small></span>}
        </div>

        <div className="modal-price">
          <div className="price-cell"><span>보증금</span><b>{listing.deposit.toLocaleString()}만</b></div>
          <div className="price-cell"><span>월세</span><b>{listing.rent}만</b></div>
          <div className="price-cell"><span>관리비</span><b>{listing.mgmtFee}만</b></div>
        </div>

        <div className="modal-actions">
          <button
            type="button"
            className={`act-btn fav${faved ? ' on' : ''}`}
            onClick={() => toggleFavorite(listingId)}
          >
            <Heart size={15} fill={faved ? 'currentColor' : 'none'} /> {faved ? '찜 완료' : '찜하기'}
          </button>
          {hasRanked && (
            <button type="button" className="act-btn primary" onClick={() => void analyzeListing(listingId)} disabled={busy}>
              {busy ? <Loader size={15} className="spin" /> : <Sparkles size={15} />} AI 입지 분석
            </button>
          )}
          <button type="button" className="act-btn" onClick={() => void share()}>
            <Share2 size={15} /> {copied ? '복사됨!' : '공유'}
          </button>
          {directionsUrl && (
            <a className="act-btn" href={directionsUrl} target="_blank" rel="noopener noreferrer">
              <Navigation size={15} /> 길찾기
            </a>
          )}
        </div>

        <div className="modal-body">
          <div className="modal-col">
            <LiveMap selected={listingId} onSelect={onSelect} />
            {loc.dataSource && (
              <div className="data-badge"><Database size={13} /> 입지 데이터: {loc.dataSource}</div>
            )}
            {loc.facts?.counts && (
              <div className="infra-grid">
                {INFRA.map(it => (
                  <div key={it.key} className="infra-cell">
                    <b>{loc.facts?.counts?.[it.key] ?? 0}</b>
                    <span>{it.label}</span>
                  </div>
                ))}
              </div>
            )}
            <p className="modal-desc">{listing.desc}</p>
            {listing.options.length > 0 && (
              <div className="opt-chips">
                {listing.options.map(o => <span key={o} className="opt-chip">{o}</span>)}
              </div>
            )}
          </div>

          <div className="modal-col">
            {loc.commute?.legs && loc.commute.legs.length > 0 && (
              <section className="detail-sec">
                <h3 className="detail-h"><MapPin size={15} /> 통학 동선 · 약 {loc.commute.totalMinutes}분</h3>
                <div className="legs">
                  {loc.commute.legs.map((leg, i) => (
                    <div key={i} className="leg">
                      <span className="leg-ic">{leg.type === 'subway' ? <Train size={13} /> : <Footprints size={13} />}</span>
                      <span className="leg-label">{leg.label}</span>
                      {leg.minutes > 0 && <span className="leg-min">{leg.minutes}분</span>}
                    </div>
                  ))}
                </div>
                {loc.commute.mainNote && <p className="detail-note">{loc.commute.mainNote}</p>}
              </section>
            )}

            {loc.nightSafety && loc.nightSafety.length > 0 && (
              <section className="detail-sec">
                <h3 className="detail-h"><ShieldCheck size={15} /> 야간 안전</h3>
                {loc.nightSafety.map((n, i) => (
                  <div key={i} className="safety-row">
                    <span className={`safety-ic ${n.pass ? 'ok' : 'warn'}`}>{n.pass ? <Check size={13} /> : <AlertTriangle size={13} />}</span>
                    <div>
                      <div className="safety-label">{n.label}</div>
                      {n.detail && <div className="safety-detail">{n.detail}</div>}
                    </div>
                  </div>
                ))}
              </section>
            )}

            {loc.convenience && loc.convenience.length > 0 && (
              <section className="detail-sec">
                <h3 className="detail-h"><ShoppingBag size={15} /> 생활 편의</h3>
                <div className="conv-row">
                  {loc.convenience.map((c, i) => (
                    <span key={i} className="conv-chip">{c.name} <b>{c.walkMin}분</b></span>
                  ))}
                </div>
              </section>
            )}
          </div>
        </div>

        {((loc.pros?.length ?? 0) > 0 || (loc.cons?.length ?? 0) > 0) && (
          <div className="proscons">
            {loc.pros && loc.pros.length > 0 && (
              <div className="pc-col">
                {loc.pros.map((p, i) => <div key={i} className="pc-row pro"><Check size={13} /> {p}</div>)}
              </div>
            )}
            {loc.cons && loc.cons.length > 0 && (
              <div className="pc-col">
                {loc.cons.map((c, i) => <div key={i} className="pc-row con"><AlertTriangle size={13} /> {c}</div>)}
              </div>
            )}
          </div>
        )}

        {aiComment && (
          <div className="ai-comment"><Sparkles size={14} /> <span>{aiComment}</span></div>
        )}
      </div>
    </div>
  )
}
