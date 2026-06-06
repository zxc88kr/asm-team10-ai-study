import { useEffect, useRef } from 'react'
import L from 'leaflet'
import useLiveStore from '../../store/useLiveStore'

// 부산대 정문(데모 기준점) — 시드 매물은 가상 좌표입니다.
const CAMPUS: [number, number] = [35.2332, 129.0794]

interface Props {
  selected: string | null
  onSelect: (id: string) => void
}

function pinHtml(rank: number | null, active: boolean): string {
  const cls = ['map-pin', active ? 'active' : '', rank === 1 ? 'gold' : ''].filter(Boolean).join(' ')
  return `<div class="${cls}">${rank != null ? rank : '·'}</div>`
}

export default function LiveMap({ selected, onSelect }: Props) {
  const listings = useLiveStore(s => s.listings)
  const ranked = useLiveStore(s => s.ranked)
  const elRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<L.Map | null>(null)
  const layerRef = useRef<L.LayerGroup | null>(null)
  const onSelectRef = useRef(onSelect)
  useEffect(() => { onSelectRef.current = onSelect }, [onSelect])

  // 지도 1회 초기화
  useEffect(() => {
    if (!elRef.current || mapRef.current) return
    const map = L.map(elRef.current, { scrollWheelZoom: false, attributionControl: true }).setView(CAMPUS, 15)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19,
    }).addTo(map)
    L.marker(CAMPUS, {
      icon: L.divIcon({ className: 'map-divicon', html: '<div class="map-campus">🎓 부산대</div>', iconSize: [78, 26], iconAnchor: [39, 13] }),
      interactive: false,
    }).addTo(map)
    layerRef.current = L.layerGroup().addTo(map)
    mapRef.current = map
    return () => {
      map.remove()
      mapRef.current = null
      layerRef.current = null
    }
  }, [])

  // 매물 마커 동기화
  useEffect(() => {
    const layer = layerRef.current
    if (!layer) return
    layer.clearLayers()
    const ids = ranked.length ? ranked.map(r => r.listingId) : Object.keys(listings)
    ids.forEach(id => {
      const item = listings[id]
      const lat = item?.geo?.lat
      const lng = item?.geo?.lng
      if (item == null || typeof lat !== 'number' || typeof lng !== 'number') return
      const idx = ranked.findIndex(r => r.listingId === id)
      const rank = idx >= 0 ? idx + 1 : null
      const active = selected === id
      L.marker([lat, lng], {
        icon: L.divIcon({ className: 'map-divicon', html: pinHtml(rank, active), iconSize: [30, 30], iconAnchor: [15, 15] }),
        zIndexOffset: active ? 1000 : 0,
      })
        .bindTooltip(item.name, { direction: 'top', offset: [0, -16] })
        .on('click', () => onSelectRef.current(id))
        .addTo(layer)
    })
  }, [listings, ranked, selected])

  // 마커 집합이 바뀌면 전체가 보이도록 맞춤
  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const pts: [number, number][] = [CAMPUS]
    const ids = ranked.length ? ranked.map(r => r.listingId) : Object.keys(listings)
    ids.forEach(id => {
      const lat = listings[id]?.geo?.lat
      const lng = listings[id]?.geo?.lng
      if (typeof lat === 'number' && typeof lng === 'number') pts.push([lat, lng])
    })
    if (pts.length > 1) map.fitBounds(L.latLngBounds(pts).pad(0.3), { animate: false })
  }, [listings, ranked])

  // 선택 매물로 부드럽게 이동
  useEffect(() => {
    const map = mapRef.current
    if (!map || !selected) return
    const lat = listings[selected]?.geo?.lat
    const lng = listings[selected]?.geo?.lng
    if (typeof lat === 'number' && typeof lng === 'number') map.panTo([lat, lng], { animate: true })
  }, [selected, listings])

  return <div className="map-canvas" ref={elRef} />
}
