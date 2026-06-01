import useAppStore, { STATUS_KO, scoreClass } from '../store/useAppStore'
import { LISTINGS } from '../data/listings'

export default function RecommendationList() {
  const lastTop = useAppStore(s => s.lastTop)
  const excludedCount = useAppStore(s => s.excludedCount)
  const openModal = useAppStore(s => s.openModal)

  return (
    <div className="card">
      <div className="card-head">
        <h2>추천 매물 <span className="muted">TOP 3</span></h2>
        {lastTop && (
          <span className="badge-soft">
            {LISTINGS.length}개 중 {excludedCount}개 제외 · 의미 매칭 랭킹
          </span>
        )}
      </div>

      {!lastTop && <div className="empty">조건이 모이면 매물을 추천해요.</div>}

      <ul className="rec-list">
        {lastTop?.map((s, idx) => (
          <RecItem key={s.L.id} s={s} idx={idx} onClick={() => openModal(s)} />
        ))}
      </ul>
    </div>
  )
}

function RecItem({ s, idx, onClick }) {
  const chips = s.breakdown.map(b => (
    <span key={b.cid} className={`mini ${b.status}`}>
      {b.label.split(/[ ·(]/)[0]} {STATUS_KO[b.status]}
    </span>
  ))

  return (
    <li className="rec-item" onClick={onClick}>
      <div className="rank">{idx + 1}</div>
      <div className="thumb">{s.L.thumb}</div>
      <div className="rec-body">
        <div className="rec-name">{s.L.name}</div>
        <div className="rec-sub">
          {s.L.area} · {s.L.type} · 보증금 {s.L.deposit.toLocaleString()} / 월세 {s.L.rent}
        </div>
        <div className="rec-chips">{chips}</div>
      </div>
      <div className={`score ${scoreClass(s.score)}`}>{s.score}<span>점</span></div>
    </li>
  )
}
