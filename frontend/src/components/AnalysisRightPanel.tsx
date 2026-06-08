import { useEffect, useRef } from 'react'
import useAppStore from '../store/useAppStore'
import { LISTINGS } from '../data/listings'
import ConditionSummary from './ConditionSummary'
import RecommendationList from './RecommendationList'

declare global {
  interface Window {
    kakao: {
      maps: {
        load: (cb: () => void) => void
        Map: new (el: HTMLElement, opts: { center: unknown; level: number }) => unknown
        LatLng: new (lat: number, lng: number) => unknown
        Marker: new (opts: { position: unknown; map?: unknown }) => unknown
        InfoWindow: new (opts: { content: string; removable?: boolean }) => {
          open: (map: unknown, marker: unknown) => void
        }
      }
    }
  }
}

interface KakaoMapProps {
  lat: number | null | undefined
  lng: number | null | undefined
  title: string
}

function KakaoMap({ lat, lng, title }: KakaoMapProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const apiKey = import.meta.env.VITE_KAKAO_MAP_KEY as string | undefined

  useEffect(() => {
    if (!apiKey || !lat || !lng || !containerRef.current) return

    const initMap = () => {
      if (!containerRef.current) return
      const center = new window.kakao.maps.LatLng(lat, lng)
      const map = new window.kakao.maps.Map(containerRef.current, { center, level: 4 })
      const marker = new window.kakao.maps.Marker({ position: center, map })
      const info = new window.kakao.maps.InfoWindow({
        content: `<div style="padding:4px 8px;font-size:12px;white-space:nowrap;">${title}</div>`,
        removable: true,
      })
      info.open(map, marker)
    }

    if (window.kakao?.maps) {
      window.kakao.maps.load(initMap)
      return
    }

    const script = document.createElement('script')
    script.src = `//dapi.kakao.com/v2/maps/sdk.js?appkey=${apiKey}&autoload=false`
    script.onload = () => window.kakao.maps.load(initMap)
    document.head.appendChild(script)
  }, [lat, lng, title, apiKey])

  if (!apiKey) {
    return (
      <div className="map-placeholder">
        <span style={{ fontSize: 24 }}>🗺️</span>
        <span>카카오맵 API 키를 설정하면 지도가 표시됩니다</span>
        <code>VITE_KAKAO_MAP_KEY=발급받은키</code>
      </div>
    )
  }

  return <div ref={containerRef} style={{ width: '100%', height: 160, borderRadius: 8 }} />
}

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
          <h2>주변 동선 지도</h2>
        </div>
        <KakaoMap
          lat={selectedListing.lat}
          lng={selectedListing.lng}
          title={selectedListing.name}
        />
      </div>

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
