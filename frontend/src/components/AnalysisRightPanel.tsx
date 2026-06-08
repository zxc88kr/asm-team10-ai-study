import useAppStore from '../store/useAppStore'
import { LISTINGS } from '../data/listings'
import ConditionSummary from './ConditionSummary'
import RecommendationList from './RecommendationList'

export default function AnalysisRightPanel() {
  const { lastTop, selectedListingId, agentListings } = useAppStore()

  const selectedListing =
    agentListings.find((l) => l.id === selectedListingId) ??
    LISTINGS.find((l) => l.id === selectedListingId) ??
    agentListings[0] ??
    LISTINGS[0]
  const analysis = selectedListing.locationAnalysis
  const score = lastTop?.find((sl) => sl.L.id === selectedListing.id)?.score ?? 86

  const circumference = 2 * Math.PI * 28
  const dashOffset = circumference - (score / 100) * circumference

  return (
    <div className="analysis-panels">
      <ConditionSummary />

      <RecommendationList selectedId={selectedListingId} />

      <div className="card">
        <div className="card-head">
          <h2>종합 판단</h2>
        </div>
        <div className="score-gauge">
          <div className="gauge-circle">
            <svg className="gauge-svg" width="68" height="68" viewBox="0 0 68 68">
              <circle className="gauge-track" cx="34" cy="34" r="28" />
              <circle
                className="gauge-fill"
                cx="34"
                cy="34"
                r="28"
                strokeDasharray={circumference}
                strokeDashoffset={dashOffset}
              />
            </svg>
            <div className="gauge-text">
              <span className="gauge-num">{score}</span>
              <span className="gauge-label">종합점수</span>
            </div>
          </div>
          <div className="score-level">
            <b>{score >= 85 ? '매우 높음' : score >= 75 ? '높음' : '보통'}</b>
            {selectedListing.name}
          </div>
        </div>
        {analysis.scoreBreakdown.length > 0 ? (
          <div className="score-bars">
            {analysis.scoreBreakdown.map((item) => (
              <div key={item.label} className="score-bar-row">
                <span className="score-bar-label">{item.label}</span>
                <div className="score-bar-track">
                  <div className="score-bar-fill" style={{ width: `${item.score}%` }} />
                </div>
                <span className="score-bar-num">{item.score}</span>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ fontSize: 12, color: 'var(--muted)', marginTop: 8 }}>
            매물을 선택하면 항목별 점수가 표시됩니다.
          </p>
        )}
      </div>
    </div>
  )
}
