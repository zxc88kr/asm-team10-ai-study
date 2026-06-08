import {
  BarChart2,
  Wallet,
  Home,
  Clock,
  Bookmark,
  Bot,
  RefreshCw,
} from 'lucide-react'
import useAppStore from '../store/useAppStore'
import { LISTINGS } from '../data/listings'
import { AppIcon } from './AppIcon'
import KakaoMap from './KakaoMap'
import type { RecommendationBasis } from '../types'


export default function LocationAnalysisView() {
  const { selectedListingId, closeAnalysis, lastTop, showToast, agentListings } = useAppStore()

  const listing =
    agentListings.find((l) => l.id === selectedListingId) ??
    LISTINGS.find((l) => l.id === selectedListingId) ??
    agentListings[0] ??
    LISTINGS[0]
  const scoredListing = lastTop?.find((sl) => sl.L.id === listing.id)
  const score = scoredListing?.score ?? 86
  const rank = lastTop ? lastTop.findIndex((sl) => sl.L.id === listing.id) + 1 : 1
  const analysis = listing.locationAnalysis
  const { basis, aiComment } = analysis

  return (
    <div className="analysis-view">
      <div className="analysis-body">
        {/* 매물 히어로 카드 */}
        <div className="listing-hero">
          <div className="listing-hero-top">
            <div className="listing-hero-thumb">{listing.thumb}</div>
            <div className="listing-hero-name-row">
              <h2 className="listing-hero-name">
                {listing.name}
                {rank > 0 && <span className="listing-hero-top1">TOP {rank}</span>}
              </h2>
            </div>
          </div>
          <div className="listing-hero-specs">
            <div className="listing-spec">
              <span className="listing-spec-label">
                <BarChart2 size={12} /> 종합점수
              </span>
              <span className="listing-spec-val">{score}점</span>
            </div>
            <div className="listing-spec">
              <span className="listing-spec-label">
                <Wallet size={12} /> 보증금
              </span>
              <span className="listing-spec-val">{listing.deposit.toLocaleString()}만 원</span>
            </div>
            <div className="listing-spec">
              <span className="listing-spec-label">
                <Home size={12} /> 월세
              </span>
              <span className="listing-spec-val">{listing.rent}만 원</span>
            </div>
            <div className="listing-spec">
              <span className="listing-spec-label">
                <Clock size={12} /> 출퇴근
              </span>
              <span className="listing-spec-val">{listing.commuteMin}분</span>
            </div>
          </div>
        </div>

        {/* AI 코멘트 */}
        <div className="ai-comment">
          <span className="ai-comment-icon">
            <Bot size={20} />
          </span>
          <span>{aiComment}</span>
        </div>

        {/* 분석 섹션 그리드 */}
        <div className="analysis-grid">
          {/* 왼쪽: 주변 지도 (2행 스팬) */}
          <div className="analysis-section" style={{ gridRow: 'span 2', display: 'flex', flexDirection: 'column', gap: 12 }}>
            <div className="section-head">
              <div className="section-num">1</div>
              <span className="section-title">주변 동선 지도</span>
            </div>
            <KakaoMap lat={listing.lat} lng={listing.lng} title={listing.name} height={460} />
          </div>

          {/* 오른쪽 상단: 추천 근거 (content 크기) */}
          <div className="analysis-section" style={{ alignSelf: 'start' }}>
            <div className="section-head">
              <div className="section-num">2</div>
              <span className="section-title">추천 근거</span>
              <span className="section-sub">(민지님의 조건과 매칭)</span>
            </div>
            <div className="basis-list">
              {basis.map((b: RecommendationBasis, i: number) => (
                <div key={i} className="basis-item">
                  <div className="basis-icon" style={{ background: 'var(--primary-soft)' }}>
                    <AppIcon name={b.icon} size={16} color="var(--primary)" />
                  </div>
                  <div className="basis-text">
                    <div className="basis-cat">{b.category}</div>
                    <div className="basis-detail">{b.detail}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 오른쪽 하단: 액션 버튼 (지도 하단에 맞춤) */}
          <div style={{ display: 'flex', flexDirection: 'row', justifyContent: 'flex-end', alignItems: 'flex-end', gap: 8 }}>
            <button className="btn-outline" onClick={closeAnalysis} type="button">
              <RefreshCw size={18} /> 조건 수정
            </button>
            <button
              className="btn-primary-fill"
              onClick={() => showToast(`${listing.name}이 저장되었습니다.`)}
              type="button"
            >
              <Bookmark size={18} /> 매물 저장
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
