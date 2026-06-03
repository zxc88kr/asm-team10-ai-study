import useAppStore, { STATUS_KO, scoreClass } from '../store/useAppStore'

export default function ListingModal() {
  const modalListing = useAppStore(s => s.modalListing)
  const closeModal = useAppStore(s => s.closeModal)

  if (!modalListing) return null

  const { L, score, breakdown, penalty } = modalListing
  const goods = breakdown.filter(b => b.status === 'full')
  const weaks = breakdown.filter(b => b.status !== 'full')
  const narrative = `민지님은 밤 11시 알바 귀가와 첫 자취가 핵심이었어요. 이 집은 ${
    goods.map(g => `'${g.label}'`).join(', ') || '기본 조건'
  }을(를) 충족해요.${weaks.length ? ` 다만 ${weaks.map(w => `'${w.label}'`).join(', ')}은(는) 아쉬운 점이에요.` : ''}`

  return (
    <div
      className="modal-backdrop"
      onClick={e => e.target === e.currentTarget && closeModal()}
    >
      <div className="modal" role="dialog" aria-modal="true">
        <button className="modal-close" onClick={closeModal}>✕</button>

        <div className="m-head">
          <div className="m-thumb">{L.thumb}</div>
          <div>
            <h3>
              {L.name}{' '}
              <span className={`score inline ${scoreClass(score)}`}>{score}점</span>
            </h3>
            <p>
              {L.area} · {L.type} · {L.pyeong}평 · {L.floor}층 · 보증금 {L.deposit.toLocaleString()} / 월세 {L.rent}
              {penalty > 0 && <span className="pen"> (월세 초과 −{penalty})</span>}
            </p>
          </div>
        </div>

        <p className="m-desc">"{L.desc}"</p>

        <div className="m-why">
          <b>왜 이 집인가</b>
          <p>{narrative}</p>
        </div>

        <div className="m-bd-title">조건별 매칭 (의미 매칭 근거)</div>
        <ul className="m-bd">
          {breakdown.map(b => (
            <li key={b.cid} className={`bd ${b.status}`}>
              <span className="bd-status">{STATUS_KO[b.status]}</span>
              <span className="bd-label">{b.label}</span>
              <span className="bd-ev">{b.evidence}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
