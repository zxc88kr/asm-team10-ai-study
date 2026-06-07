import { useEffect, useRef } from 'react'
import useAppStore, { scoreClass } from '../store/useAppStore'
import { LISTINGS } from '../data/listings'
import ConditionSummary from './ConditionSummary'

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
      <div className="map-placeholder" style={{
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        justifyContent: 'center', height: 160, background: '#E8F0FE',
        borderRadius: 8, gap: 6, color: '#718096', fontSize: 12,
      }}>
        <span style={{ fontSize: 24 }}>🗺️</span>
        <span>카카오맵 API 키를 설정하면 지도가 표시됩니다</span>
        <code style={{ fontSize: 10, color: '#A0AEC0' }}>VITE_KAKAO_MAP_KEY=발급받은키</code>
      </div>
    )
  }

  return <div ref={containerRef} style={{ width: '100%', height: 160, borderRadius: 8 }} />
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
      <ConditionSummary showEdit />

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
                  역 {sl.L.commuteMin}분 · 월 {sl.L.rent}만 원
                </div>
              </div>
              <div className={`compare-score ${scoreClass(sl.score)}`}>{sl.score}</div>
            </div>
          ))}
        </div>
      </div>

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
        ) : (
          <p style={{ fontSize: 12, color: 'var(--muted)', marginTop: 8 }}>
            매물을 선택하면 항목별 점수가 표시됩니다.
          </p>
        )}
      </div>
    </div>
  )
}
