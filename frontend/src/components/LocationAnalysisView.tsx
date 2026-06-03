import useAppStore from '../store/useAppStore'
import { LISTINGS } from '../data/listings'
import type { NightSafetyItem, ConvenienceFacility, RecommendationBasis } from '../types'

export default function LocationAnalysisView() {
  const { selectedListingId, closeAnalysis, lastTop, showToast } = useAppStore()

  const listing = LISTINGS.find(l => l.id === selectedListingId) ?? LISTINGS[0]
  const scoredListing = lastTop?.find(sl => sl.L.id === listing.id)
  const score = scoredListing?.score ?? 86
  const analysis = listing.locationAnalysis
  const { commute, nightSafety, convenience, basis, pros, cons, aiComment } = analysis

  return (
    <div className="analysis-view">
      {/* 헤더 */}
      <div className="analysis-head">
        <div className="analysis-head-left">
          <button className="btn-icon" onClick={closeAnalysis} type="button">← 뒤로</button>
          <div>
            <h1>AI 입지 해설사</h1>
            <p>입지 분석 리포트</p>
          </div>
        </div>
      </div>

      <div className="analysis-body">
        {/* 매물 히어로 카드 */}
        <div className="listing-hero">
          <div className="listing-hero-thumb">
            <span className="top1-crown">👑</span>
            {listing.thumb}
          </div>
          <div className="listing-hero-info">
            <h2>
              {listing.name}
              <span className="listing-hero-top1">TOP 1</span>
            </h2>
            <div className="listing-hero-specs">
              <div className="listing-spec">
                <span className="listing-spec-label">📊 종합점수</span>
                <span className="listing-spec-val" style={{ color: 'var(--green)' }}>{score}점</span>
              </div>
              <div className="listing-spec">
                <span className="listing-spec-label">💰 보증금</span>
                <span className="listing-spec-val">{listing.deposit.toLocaleString()}만 원</span>
              </div>
              <div className="listing-spec">
                <span className="listing-spec-label">🏠 월세</span>
                <span className="listing-spec-val">{listing.rent}만 원</span>
              </div>
              <div className="listing-spec">
                <span className="listing-spec-label">⏱️ 출퇴근</span>
                <span className="listing-spec-val">{listing.commuteMin}분</span>
              </div>
            </div>
          </div>
          <button className="listing-bookmark" type="button">🔖</button>
        </div>

        {/* 분석 섹션 그리드 */}
        <div className="analysis-grid">
          {/* 1. 출퇴근 분석 */}
          <div className="analysis-section">
            <div className="section-head">
              <div className="section-num">1</div>
              <span className="section-title">출퇴근 분석</span>
              <span className="section-sub">📍 강남역(회사) 기준</span>
            </div>
            <div className="commute-route">
              <div className="route-node">
                <div className="route-dot home">🏠</div>
                <span className="route-label">집</span>
              </div>
              {commute.legs.map((leg, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 4, flex: 1 }}>
                  <div className="route-line" />
                  <div className="route-node">
                    <div className={`route-dot${i === commute.legs.length - 1 ? ' office' : ''}`}>
                      {leg.type === 'subway' ? '🚇' : leg.type === 'bus' ? '🚌' : '🏢'}
                    </div>
                    <span className="route-label">{leg.label}</span>
                  </div>
                </div>
              ))}
            </div>
            <div className="commute-tags">
              <span className="commute-tag highlight">🏃 회사까지 도보 {commute.totalMinutes}분</span>
              <span className="commute-tag">환승 {commute.transfers}회</span>
              <span className="commute-tag highlight">{commute.mainNote}</span>
            </div>
          </div>

          {/* 2. 심야 귀가 안전 */}
          <div className="analysis-section">
            <div className="section-head">
              <div className="section-num">2</div>
              <span className="section-title">심야 귀가 안전</span>
            </div>
            <div className="night-safety-list">
              {nightSafety.map((item: NightSafetyItem, i: number) => (
                <div key={i} className="night-item">
                  <span className="night-item-icon">{item.icon}</span>
                  <div className="night-item-text">
                    <div className="night-item-label">{item.label}</div>
                    {item.detail && <div className="night-item-detail">{item.detail}</div>}
                  </div>
                  <div className={`night-check ${item.pass ? 'pass' : 'fail'}`}>
                    {item.pass ? '✓' : '✗'}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 3. 생활 편의시설 */}
          <div className="analysis-section">
            <div className="section-head">
              <div className="section-num">3</div>
              <span className="section-title">생활 편의시설</span>
              <span className="section-sub">반경 500m 기준</span>
            </div>
            <div className="convenience-grid">
              {convenience.map((fac: ConvenienceFacility, i: number) => (
                <div key={i} className="conv-item">
                  <span className="conv-icon">{fac.icon}</span>
                  <span className="conv-name">{fac.name}</span>
                  <span className="conv-min">도보 {fac.walkMin}분</span>
                </div>
              ))}
            </div>
          </div>

          {/* 4. 추천 근거 */}
          <div className="analysis-section">
            <div className="section-head">
              <div className="section-num">4</div>
              <span className="section-title">추천 근거</span>
              <span className="section-sub">(민지님의 조건과 매칭)</span>
            </div>
            <div className="basis-list">
              {basis.map((b: RecommendationBasis, i: number) => (
                <div key={i} className="basis-item">
                  <div className="basis-icon" style={{ background: b.color + '20' }}>
                    {b.icon}
                  </div>
                  <div className="basis-text">
                    <div className="basis-cat">{b.category}</div>
                    <div className="basis-detail">{b.detail}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 5. 장점 / 아쉬운 점 */}
        <div className="analysis-section">
          <div className="section-head">
            <div className="section-num">5</div>
            <span className="section-title">장점 / 아쉬운 점</span>
          </div>
          <div className="pros-cons">
            <div className="pros-col">
              <div className="pros-col-title">장점</div>
              {pros.map((p, i) => (
                <div key={i} className="pros-item">{p}</div>
              ))}
            </div>
            <div className="cons-col">
              <div className="cons-col-title" style={{ color: 'var(--amber)' }}>아쉬운 점</div>
              {cons.map((c, i) => (
                <div key={i} className="cons-item">{c}</div>
              ))}
            </div>
          </div>
        </div>

        {/* AI 코멘트 */}
        <div className="ai-comment">
          <span className="ai-comment-icon">🤖</span>
          <span>{aiComment}</span>
        </div>

        {/* 액션 버튼 */}
        <div className="analysis-actions">
          <button className="btn-outline" onClick={closeAnalysis} type="button">
            🔄 조건 수정 후 다시 추천
          </button>
          <button
            className="btn-primary-fill"
            onClick={() => showToast(`${listing.name}이 저장되었습니다.`)}
            type="button"
          >
            🔖 이 매물 저장
          </button>
        </div>
      </div>
    </div>
  )
}
