import useAppStore, { scoreClass } from '../store/useAppStore'
import type { ScoredListing } from '../types'

interface Props {
  onSelectListing?: (id: string) => void
  selectedId?: string | null
}

export default function RecommendationList({ onSelectListing, selectedId }: Props) {
  const { lastTop, recommended, openAnalysis } = useAppStore()

  const handleClick = (sl: ScoredListing) => {
    if (onSelectListing) {
      onSelectListing(sl.L.id)
    } else {
      openAnalysis(sl.L.id)
    }
  }

  if (!recommended || !lastTop || lastTop.length === 0) {
    return (
      <div className="card">
        <div className="card-head">
          <h2>추천 매물 TOP 3</h2>
          <span style={{ fontSize: 11, color: 'var(--muted)' }}>전체 보기</span>
        </div>
        <p style={{ fontSize: 12, color: 'var(--muted)', padding: '4px 0', lineHeight: 1.6 }}>
          대화가 완료되면 맞춤 매물을 추천해드려요.
        </p>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="card-head">
        <h2>추천 매물 TOP 3</h2>
        <button className="card-link" type="button">
          전체 보기
        </button>
      </div>
      <ul className="rec-list">
        {lastTop.map((sl, idx) => (
          <li
            key={sl.L.id}
            className={`rec-item${idx === 0 ? ' top1' : ''}${selectedId === sl.L.id ? ' selected' : ''}`}
            onClick={() => handleClick(sl)}
          >
            <div className={`rank-badge${idx === 0 ? ' gold' : idx === 1 ? ' silver' : ' bronze'}`}>
              {idx + 1}
            </div>
            <div className="thumb">{sl.L.thumb}</div>
            <div className="rec-body">
              <div className="flex items-center gap-2">
                <div className="rec-name">{sl.L.name}</div>
                <span className="rec-name-arrow">→</span>
              </div>
              <div className="rec-tags">
                <span className="rec-tag">출퇴근 {sl.L.commuteMin}분</span>
                <span className="rec-tag">월 {sl.L.rent}만</span>
              </div>
            </div>
            <div className={`score-badge ${scoreClass(sl.score)}`}>
              {sl.score}
              <span style={{ fontSize: 13, fontWeight: 400, color: 'var(--muted)' }}>점</span>
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
