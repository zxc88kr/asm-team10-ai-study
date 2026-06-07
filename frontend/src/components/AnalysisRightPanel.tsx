import useAppStore, { scoreClass } from '../store/useAppStore'
import { LISTINGS } from '../data/listings'
import ConditionSummary from './ConditionSummary'

function MapSvg() {
  return (
    <div className="map-placeholder">
      <svg className="map-svg" viewBox="0 0 300 160" xmlns="http://www.w3.org/2000/svg">
        <rect width="300" height="160" fill="#E8F0FE" />
        {/* 도로 */}
        <line x1="0" y1="80" x2="300" y2="80" stroke="#C5D3F0" strokeWidth="8" />
        <line x1="150" y1="0" x2="150" y2="160" stroke="#C5D3F0" strokeWidth="6" />
        <line x1="50" y1="0" x2="50" y2="160" stroke="#D8E4FA" strokeWidth="3" />
        <line x1="240" y1="0" x2="240" y2="160" stroke="#D8E4FA" strokeWidth="3" />
        <line x1="0" y1="40" x2="300" y2="40" stroke="#D8E4FA" strokeWidth="3" />
        <line x1="0" y1="120" x2="300" y2="120" stroke="#D8E4FA" strokeWidth="3" />

        {/* 귀가 동선 (집 → 역) */}
        <path d="M 80 100 L 80 80 L 150 80" stroke="#4B7BF5" strokeWidth="2" strokeDasharray="5,3" fill="none" />
        {/* 출근 동선 (역 → 회사) */}
        <path d="M 150 80 L 240 80 L 240 50" stroke="#22C55E" strokeWidth="2" strokeDasharray="5,3" fill="none" />

        {/* 집 */}
        <circle cx="80" cy="100" r="9" fill="#4B7BF5" />
        <text x="80" y="104" textAnchor="middle" fill="white" fontSize="9" fontWeight="bold">집</text>
        <text x="80" y="118" textAnchor="middle" fill="#4B7BF5" fontSize="9" fontWeight="600">집</text>

        {/* 선릉역 */}
        <circle cx="150" cy="80" r="9" fill="#22C55E" />
        <text x="150" y="84" textAnchor="middle" fill="white" fontSize="8" fontWeight="bold">역</text>
        <text x="150" y="99" textAnchor="middle" fill="#22C55E" fontSize="9" fontWeight="600">선릉역</text>

        {/* 강남역(회사) */}
        <circle cx="240" cy="50" r="9" fill="#F59E0B" />
        <text x="240" y="54" textAnchor="middle" fill="white" fontSize="8" fontWeight="bold">회</text>
        <text x="240" y="69" textAnchor="middle" fill="#F59E0B" fontSize="9" fontWeight="600">강남역</text>

        {/* 편의시설 */}
        <circle cx="60" cy="60" r="5" fill="#8B5CF6" opacity="0.7" />
        <circle cx="110" cy="115" r="5" fill="#8B5CF6" opacity="0.7" />
        <circle cx="180" cy="50" r="5" fill="#8B5CF6" opacity="0.7" />

        {/* 범례 */}
        <rect x="5" y="130" width="290" height="26" fill="white" opacity="0.8" rx="4" />
        <circle cx="16" cy="143" r="4" fill="#4B7BF5" />
        <text x="23" y="147" fill="#4A5568" fontSize="8">집</text>
        <circle cx="46" cy="143" r="4" fill="#22C55E" />
        <text x="53" y="147" fill="#4A5568" fontSize="8">역(선릉역)</text>
        <circle cx="100" cy="143" r="4" fill="#F59E0B" />
        <text x="107" y="147" fill="#4A5568" fontSize="8">회사(강남역)</text>
        <line x1="163" y1="143" x2="175" y2="143" stroke="#4B7BF5" strokeWidth="1.5" strokeDasharray="3,2" />
        <text x="178" y="147" fill="#4A5568" fontSize="8">추천 동선</text>
        <line x1="218" y1="143" x2="230" y2="143" stroke="#22C55E" strokeWidth="1.5" strokeDasharray="3,2" />
        <text x="233" y="147" fill="#4A5568" fontSize="8">귀가 동선</text>

        {/* 500m 스케일 */}
        <line x1="230" y1="125" x2="270" y2="125" stroke="#9AA3B2" strokeWidth="1.5" />
        <text x="250" y="120" textAnchor="middle" fill="#9AA3B2" fontSize="8">500m</text>

        {/* 편의시설 마커 라벨 */}
        <circle cx="60" cy="60" r="5" fill="#14B8A6" opacity="0.8" />
        <text x="68" y="63" fill="#14B8A6" fontSize="8">+편의</text>
      </svg>
    </div>
  )
}

export default function AnalysisRightPanel() {
  const { lastTop, selectedListingId, openAnalysis, agentListings } = useAppStore()

  const selectedListing =
    agentListings.find(l => l.id === selectedListingId) ??
    LISTINGS.find(l => l.id === selectedListingId) ??
    agentListings[0] ??
    LISTINGS[0]
  const analysis = selectedListing.locationAnalysis
  const score = lastTop?.find(sl => sl.L.id === selectedListing.id)?.score ?? 86

  const circumference = 2 * Math.PI * 28
  const dashOffset = circumference - (score / 100) * circumference

  return (
    <div className="analysis-panels">
      {/* 내 조건 요약 */}
      <ConditionSummary showEdit />

      {/* TOP3 비교 */}
      <div className="card">
        <div className="card-head">
          <h2>TOP 3 비교</h2>
          <button className="card-link" type="button">상세 비교</button>
        </div>
        <div className="top3-compare">
          {lastTop?.map((sl, idx) => (
            <div
              key={sl.L.id}
              className={`compare-item${sl.L.id === selectedListingId ? ' selected' : ''}`}
              onClick={() => openAnalysis(sl.L.id)}
            >
              <div className="compare-thumb">
                <div className={`compare-rank${idx === 0 ? ' gold' : ''}`}>{idx + 1}</div>
                {sl.L.thumb}
              </div>
              <div className="compare-body">
                <div className="compare-name">{sl.L.name}</div>
                <div className="compare-meta">
                  출퇴근 {sl.L.commuteMin}분 · 월 {sl.L.rent}만 원
                </div>
              </div>
              <div className={`compare-score ${scoreClass(sl.score)}`}>{sl.score}</div>
            </div>
          ))}
        </div>
      </div>

      {/* 주변 동선 지도 */}
      <div className="card">
        <div className="card-head">
          <h2>주변 동선 지도</h2>
        </div>
        <MapSvg />
        <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 8 }}>
          {[
            { color: '#4B7BF5', label: '집' },
            { color: '#22C55E', label: '역(선릉역)' },
            { color: '#F59E0B', label: '회사(강남역)' },
            { color: '#8B5CF6', label: '편의시설' },
          ].map(item => (
            <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: 'var(--ink-2)' }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: item.color, flex: 'none' }} />
              {item.label}
            </div>
          ))}
        </div>
      </div>

      {/* 종합 판단 */}
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
            <b>매우 높음</b>
            {selectedListing.name}
          </div>
        </div>
        <div className="score-bars">
          {analysis.scoreBreakdown.map(item => (
            <div key={item.label} className="score-bar-row">
              <span className="score-bar-label">{item.label}</span>
              <div className="score-bar-track">
                <div className="score-bar-fill" style={{ width: `${item.score}%` }} />
              </div>
              <span className="score-bar-num">{item.score}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
