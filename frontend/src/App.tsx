import { useEffect, useState } from 'react'
import { Map as MapIcon } from 'lucide-react'
import LiveTopBar from './components/live/LiveTopBar'
import LiveLanding from './components/live/LiveLanding'
import LiveChat from './components/live/LiveChat'
import LiveMetric from './components/live/LiveMetric'
import LiveConditions from './components/live/LiveConditions'
import LiveRecommendations from './components/live/LiveRecommendations'
import LiveMap from './components/live/LiveMap'
import LiveListingModal from './components/live/LiveListingModal'
import useLiveStore from './store/useLiveStore'

export default function App() {
  const init = useLiveStore(s => s.init)
  const started = useLiveStore(s => s.messages.some(m => m.role === 'user'))
  const [detailId, setDetailId] = useState<string | null>(null)

  useEffect(() => {
    void init()
  }, [init])

  return (
    <div className="shell">
      <LiveTopBar started={started} />
      {started ? (
        <main className="workspace">
          <LiveChat />
          <aside className="insight-col">
            <LiveMetric />
            <LiveConditions />
            <LiveRecommendations onOpen={setDetailId} />
            <div className="card" id="sec-map">
              <div className="card-head">
                <span className="head-ic"><MapIcon size={17} /></span>
                <h2>매물 위치 지도</h2>
              </div>
              <LiveMap selected={detailId} onSelect={setDetailId} />
              <p className="map-hint">핀을 누르면 매물 상세 · 주변 시설은 OpenStreetMap 실측, 좌표는 데모용</p>
            </div>
          </aside>
        </main>
      ) : (
        <LiveLanding />
      )}
      {detailId && (
        <LiveListingModal listingId={detailId} onClose={() => setDetailId(null)} onSelect={setDetailId} />
      )}
    </div>
  )
}
