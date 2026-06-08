import { useEffect, useRef, useState } from 'react'

declare global {
  interface Window {
    kakao: {
      maps: {
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
  height?: number
}

export default function KakaoMap({ lat, lng, title, height = 200 }: KakaoMapProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const apiKey = import.meta.env.VITE_KAKAO_MAP_KEY as string | undefined
  const [mapError, setMapError] = useState<string | null>(null)

  useEffect(() => {
    if (!apiKey) return

    setMapError(null)

    const mapLat = lat ?? 37.5665
    const mapLng = lng ?? 126.978

    const initMap = () => {
      if (!containerRef.current) return
      try {
        const center = new window.kakao.maps.LatLng(mapLat, mapLng)
        const map = new window.kakao.maps.Map(containerRef.current, { center, level: 4 })
        if (lat && lng) {
          const marker = new window.kakao.maps.Marker({ position: center, map })
          const info = new window.kakao.maps.InfoWindow({
            content: `<div style="padding:4px 24px 4px 8px;font-size:12px;max-width:180px;word-break:keep-all;">${title}</div>`,
            removable: true,
          })
          info.open(map, marker)
        }
      } catch {
        setMapError('지도 초기화 실패')
      }
    }

    if (window.kakao?.maps?.Map) {
      initMap()
      return
    }

    let elapsed = 0
    const poll = setInterval(() => {
      elapsed += 100
      if (window.kakao?.maps?.Map) {
        clearInterval(poll)
        initMap()
      } else if (elapsed >= 5000) {
        clearInterval(poll)
        setMapError('카카오맵 SDK 로드 실패')
      }
    }, 100)
    return () => clearInterval(poll)
  }, [lat, lng, title, apiKey])

  if (!apiKey) {
    return (
      <div className="map-placeholder" style={{ height }}>
        <span style={{ fontSize: 24 }}>🗺️</span>
        <span>VITE_KAKAO_MAP_KEY 미설정</span>
      </div>
    )
  }

  if (mapError) {
    return (
      <div className="map-placeholder" style={{ height }}>
        <span style={{ fontSize: 24 }}>⚠️</span>
        <span>{mapError}</span>
      </div>
    )
  }

  return <div ref={containerRef} style={{ width: '100%', height, borderRadius: 8 }} />
}
