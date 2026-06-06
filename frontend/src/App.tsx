import { useEffect } from 'react'
import LiveSidebar from './components/live/LiveSidebar'
import LiveChat from './components/live/LiveChat'
import LiveConditions from './components/live/LiveConditions'
import LiveRecommendations from './components/live/LiveRecommendations'
import useLiveStore from './store/useLiveStore'

export default function App() {
  const init = useLiveStore(s => s.init)

  useEffect(() => {
    void init()
  }, [init])

  return (
    <div className="app">
      <LiveSidebar />
      <LiveChat />
      <div className="panels">
        <LiveConditions />
        <LiveRecommendations />
      </div>
    </div>
  )
}
